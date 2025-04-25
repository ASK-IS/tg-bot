import logging
import random
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message, ReactionTypeEmoji
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (ADMIN_CHAT, EMOJI_SET, MAILING_DIALOG, MALREADY_MSG, MREADY_MSG, NOEDITS_MSG, PENDING_MSG, Q_MSG,
                    START_MSG, USERS_COOLDOWN, USERS_TOPICS, WAIT5_MSG, bot)
from utils import AdminFilter, convert_to_mention, get_unique_users, is_spam, retry_func, save_unique_user

router = Router()
admin_router = Router()
admin_router.message.filter(F.chat.type == 'private', AdminFilter())


@router.message(F.text.startswith('/start'), F.chat.type == 'private')
async def start(msg: Message):
    """Отправляет стартовое сообщение"""
    await msg.answer(START_MSG, disable_web_page_preview=True)
    save_unique_user(msg.from_user.id)


@router.message(F.text, F.chat.type == 'private')
@router.message(F.audio | F.video_note | F.photo | F.document | F.video | F.voice, F.chat.type == 'private')
async def question(msg: Message):
    """Отправляет нам вопрос студента"""
    user_id, msg_id = msg.from_user.id, msg.message_id

    question_content = msg.text or msg.caption

    if question_content and not question_content.lower().startswith('полтергейст'):
        if is_spam(question_content):
            if 'спасибо' in question_content.lower():
                await msg.react([ReactionTypeEmoji(emoji='❤')])
                return
            await msg.react([ReactionTypeEmoji(emoji='👎')])
            return
        if (cd_user := USERS_COOLDOWN.get(user_id)) and datetime.now() < cd_user['last_time'] + timedelta(minutes=5):
            await msg.react([ReactionTypeEmoji(emoji='🙊')])
            if not cd_user['is_msg_sent']:
                await msg.answer(WAIT5_MSG)
                cd_user['is_msg_sent'] = True
            return
    if msg.audio or msg.video_note:
        await msg.react([ReactionTypeEmoji(emoji='👎')])
        return

    if user_id in USERS_TOPICS and datetime.now() < USERS_TOPICS[user_id]['last_time'] + timedelta(days=1):
        thread_id = USERS_TOPICS[user_id]['topic_id']
    else:
        mention = f'@{msg.from_user.username}' if msg.from_user.username else msg.from_user.full_name
        topic = await bot.create_forum_topic(
            ADMIN_CHAT, f'Вопрос от {mention}', icon_custom_emoji_id='5379748062124056162'
        )
        thread_id = topic.message_thread_id
    question_content = msg.html_text or msg.caption or ''
    text = Q_MSG.format(convert_to_mention(msg.from_user), question_content, user_id, msg_id)
    if any([msg.photo, msg.document, msg.video, msg.voice]):
        await bot.copy_message(ADMIN_CHAT, user_id, msg_id, thread_id, text)
    else:
        await bot.send_message(ADMIN_CHAT, text, message_thread_id=thread_id)

    USERS_COOLDOWN[user_id] = {'last_time': datetime.now(), 'is_msg_sent': False}
    USERS_TOPICS[user_id] = {'topic_id': thread_id, 'msg_id': msg_id, 'last_time': datetime.now()}

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    logging.info(f'Question from {user_id} - {msg_id} sent to admin chat')


@router.edited_message(F.text, F.from_user, F.chat.type == 'private')
@router.edited_message(F.caption, F.from_user, F.chat.type == 'private')
async def edit_warning(msg: Message):
    """Отправляет сообщение о том, что редактированные сообщения не доходят"""
    await msg.answer(NOEDITS_MSG)


@router.message(Command('pending'), F.message_thread_id)
@router.message(Command('рассмотрение'), F.message_thread_id)
@router.message(Command('рассмотреть'), F.message_thread_id)
async def pending_question(msg: Message):
    """Фиксирует топик на рассмотрение"""
    assert msg.message_thread_id
    await bot.edit_forum_topic(ADMIN_CHAT, msg.message_thread_id, icon_custom_emoji_id='5348436127038579546')

    user_id, msg_id = next(
        ((uid, data['msg_id']) for uid, data in USERS_TOPICS.items() if data['topic_id'] == msg.message_thread_id),
        (None, None),
    )
    emoji_num = random.randint(0, len(EMOJI_SET) - 1)
    board = InlineKeyboardBuilder(
        [[InlineKeyboardButton(text='Отправить 📤️', callback_data=f'send {user_id} {msg_id} {emoji_num}')]]
    )
    await msg.answer(PENDING_MSG.format(EMOJI_SET[emoji_num]), reply_markup=board.as_markup())
    await msg.react([ReactionTypeEmoji(emoji='👍')])


@router.callback_query(F.data.startswith('send'))
async def send_pending_question(resp: CallbackQuery):
    """Отправляет шаблонное сообщение о том, что взято на рассмотрение"""
    assert isinstance(resp.message, Message)

    _, user_id, msg_id, emoji_num = resp.data.split()
    await bot.send_message(int(user_id), PENDING_MSG.format(EMOJI_SET[int(emoji_num)]), reply_to_message_id=int(msg_id))
    await resp.message.react([ReactionTypeEmoji(emoji='👍')])
    await resp.message.edit_reply_markup(reply_markup=None)


@router.message(Command('close'), F.message_thread_id)
@router.message(Command('закрыт'), F.message_thread_id)
@router.message(Command('закрыть'), F.message_thread_id)
async def close_question(msg: Message):
    """Закрывает вопрос"""
    assert msg.message_thread_id

    await bot.edit_forum_topic(ADMIN_CHAT, msg.message_thread_id, icon_custom_emoji_id='5237699328843200968')
    await bot.close_forum_topic(ADMIN_CHAT, msg.message_thread_id)
    await msg.react([ReactionTypeEmoji(emoji='👍')])


@router.message(Command('reopen'), F.message_thread_id)
@router.message(Command('переоткрыт'), F.message_thread_id)
@router.message(Command('переоткрыть'), F.message_thread_id)
async def reopen_question(msg: Message):
    """Открывает вопрос"""
    assert msg.message_thread_id
    await bot.edit_forum_topic(ADMIN_CHAT, msg.message_thread_id, icon_custom_emoji_id='5379748062124056162')
    await bot.reopen_forum_topic(ADMIN_CHAT, msg.message_thread_id)
    await msg.react([ReactionTypeEmoji(emoji='👍')])


@router.message(Command('achieve'), F.message_thread_id)
@router.message(Command('реализован'), F.message_thread_id)
@router.message(Command('реализовать'), F.message_thread_id)
async def achieve_question(msg: Message):
    """Отмечает вопрос как реализованный"""
    assert msg.message_thread_id
    await bot.edit_forum_topic(ADMIN_CHAT, msg.message_thread_id, icon_custom_emoji_id='5309958691854754293')
    await bot.close_forum_topic(ADMIN_CHAT, msg.message_thread_id)
    await msg.react([ReactionTypeEmoji(emoji='👍')])


@router.message(Command('answer'), F.message_thread_id)
@router.message(Command('ответ'), F.message_thread_id)
@router.message(F.reply_to_message, F.message_thread_id, ~F.quote)
async def answer_question(msg: Message):
    """Пересылает ответ на вопрос студента"""

    command_flag = msg.text.startswith('/answer') or msg.text.startswith('/ответ')

    if msg.reply_to_message.message_id == msg.message_thread_id and not command_flag:
        return
    if msg.text == '/answer':
        await msg.react([ReactionTypeEmoji(emoji='💩')], True)
        return

    if command_flag:
        answer = msg.html_text.removeprefix('/answer').removeprefix('/ответ').strip()
        user_id, msg_id = next(
            ((uid, data['msg_id']) for uid, data in USERS_TOPICS.items() if data['topic_id'] == msg.message_thread_id),
        )
        await bot.send_message(int(user_id), answer, reply_to_message_id=int(msg_id))
    else:
        question_text = msg.reply_to_message.text or msg.reply_to_message.caption
        try:
            user_id, msg_id = map(int, list(filter(lambda s: bool(s), question_text.split('\n')))[-1].split())
        except ValueError:
            return
        await bot.send_message(user_id, msg.html_text, reply_to_message_id=msg_id)

    if user_id in USERS_COOLDOWN:
        del USERS_COOLDOWN[user_id]

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    logging.info(f'Answer to {user_id} {msg_id} sent')


@admin_router.message(Command('рассылка'), lambda _: not MAILING_DIALOG['is_ready'])
@admin_router.message(Command('mailing'), lambda _: not MAILING_DIALOG['is_ready'])
async def start_mailing_dialog(msg: Message):
    """Запускает диалог рассылки"""
    await msg.answer(MREADY_MSG)
    MAILING_DIALOG['is_ready'] = True
    MAILING_DIALOG['user_id'] = msg.from_user.id

    logging.info('Mailing dialog started')


@admin_router.message(Command('рассылка'), lambda _: MAILING_DIALOG['is_ready'])
@admin_router.message(Command('mailing'), lambda _: MAILING_DIALOG['is_ready'])
async def mailing(msg: Message):
    """Начинает рассылку при запущенном диалоге рассылки или останавливает диалог рассылки"""
    if MAILING_DIALOG['user_id'] != msg.from_user.id:
        await msg.answer(MALREADY_MSG)

    MAILING_DIALOG['is_ready'] = False

    if not MAILING_DIALOG['msg_ids']:
        await msg.react([ReactionTypeEmoji(emoji='👌')])
        return

    await msg.react([ReactionTypeEmoji(emoji='✍️')])
    for user_id in get_unique_users():
        await retry_func(bot.copy_messages, user_id, MAILING_DIALOG['user_id'], MAILING_DIALOG['msg_ids'])
    await msg.react([ReactionTypeEmoji(emoji='👍')])

    MAILING_DIALOG['msg_ids'] = []
    MAILING_DIALOG['user_id'] = 0

    logging.info('Mailing sent')


@admin_router.message(F.text, lambda _: MAILING_DIALOG['is_ready'])
async def collect_mailing(msg: Message):
    """Собирает сообщения для рассылки"""
    MAILING_DIALOG['msg_ids'].append(msg.message_id)
    await msg.react([ReactionTypeEmoji(emoji='👀')])


# @router.message(Command('ban'), F.message_thread_id)
# async def ban_user(msg: Message):
#     """Банит пользователя"""
#     user_id = int(msg.reply_to_message.text.rsplit('\n')[-1].split()[0])

#     ...

#     await msg.react([ReactionTypeEmoji(emoji='👍')])
#     logging.info(f'User {user_id} banned')
