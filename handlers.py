import logging
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReactionTypeEmoji

from config import (ADMIN_CHAT, IS_READY_FOR_MAILING, MAILING_MSG_IDS, MREADY_MSG, NOEDITS_MSG, Q_MSG, START_MSG,
                    USERS_COOLDOWN, WAIT5_MSG, bot)
from utils import AdminFilter, convert_to_mention, get_unique_users, is_spam, save_unique_user

router = Router()


@router.message(F.text.startswith('/start'), F.chat.type == 'private')
async def start(msg: Message):
    """Отправляет стартовое сообщение"""
    await msg.answer(START_MSG, disable_web_page_preview=True)
    save_unique_user(msg.from_user.id)


@router.message(F.text, F.chat.type == 'private')
@router.message(F.audio | F.video_note | F.photo | F.document | F.video | F.voice, F.chat.type == 'private')
async def question(msg: Message):
    """Отправляет нам вопрос студента"""
    assert msg.from_user
    user_id, msg_id = msg.from_user.id, msg.message_id

    question_content = msg.text or msg.caption

    if question_content and not question_content.lower().startswith('полтергейст'):
        if is_spam(question_content):
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

    question_content = msg.html_text or msg.caption or ''
    text = Q_MSG.format(convert_to_mention(msg.from_user), question_content, user_id, msg_id)
    if any([msg.photo, msg.document, msg.video, msg.voice]):
        await bot.copy_message(ADMIN_CHAT, user_id, msg_id, caption=text)
    else:
        await bot.send_message(ADMIN_CHAT, text)

    USERS_COOLDOWN[user_id] = {'last_time': datetime.now(), 'is_msg_sent': False}

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    logging.info(f'Question from {user_id} - {msg_id} sent to admin chat')


@router.edited_message(F.text, F.from_user, F.chat.type == 'private')
@router.edited_message(F.caption, F.from_user, F.chat.type == 'private')
async def edit_warning(msg: Message):
    """Отправляет сообщение о том, что редактированные сообщения не доходят"""
    await msg.answer(NOEDITS_MSG)


@router.message(Command('answer'), F.message_thread_id)
async def answer_question(msg: Message):
    """Пересылает ответ на вопрос студента"""
    assert msg.message_thread_id

    if msg.text == '/answer':
        await msg.react([ReactionTypeEmoji(emoji='💩')], True)
        return

    user_id, msg_id = map(int, msg.reply_to_message.text.rsplit('\n')[-1].split())
    await bot.send_message(user_id, msg.html_text.removeprefix('/answer '), reply_to_message_id=msg_id)

    if user_id in USERS_COOLDOWN:
        del USERS_COOLDOWN[user_id]

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    logging.info(f'Answer to {user_id} {msg_id} sent')


@router.message(Command('mailing'), F.chat.type == 'private', AdminFilter(), lambda: not IS_READY_FOR_MAILING)
async def start_mailing_dialog(msg: Message):
    """Запускает диалог рассылки"""
    global IS_READY_FOR_MAILING

    await msg.answer(MREADY_MSG)
    IS_READY_FOR_MAILING = True

    logging.info('Mailing dialog started')


@router.message(F.text, F.chat.type == 'private', AdminFilter(), lambda: IS_READY_FOR_MAILING)
async def collect_mailing(msg: Message):
    """Собирает сообщения для рассылки"""
    MAILING_MSG_IDS.append(msg.message_id)


@router.message(Command('mailing'), F.chat.type == 'private', AdminFilter(), lambda: IS_READY_FOR_MAILING)
async def mailing(msg: Message):
    """Начинает рассылку при запущенном диалоге рассылки или останавливает диалог рассылки"""
    global IS_READY_FOR_MAILING, MAILING_MSG_IDS

    IS_READY_FOR_MAILING = False

    if not MAILING_MSG_IDS:
        await msg.react([ReactionTypeEmoji(emoji='👌')])
        return

    await msg.react([ReactionTypeEmoji(emoji='✍️')])
    for user_id in get_unique_users():
        await bot.copy_messages(user_id, ADMIN_CHAT, MAILING_MSG_IDS)
    await msg.react([ReactionTypeEmoji(emoji='👍')])

    MAILING_MSG_IDS = []

    logging.info('Mailing sent')


# @router.message(Command('ban'), F.message_thread_id)
# async def ban_user(msg: Message):
#     """Банит пользователя"""
#     assert msg.message_thread_id
#     user_id = int(msg.reply_to_message.text.rsplit('\n')[-1].split()[0])

#     ...

#     await msg.react([ReactionTypeEmoji(emoji='👍')])
#     logging.info(f'User {user_id} banned')
