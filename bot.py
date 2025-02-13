import asyncio
import string
from datetime import datetime, timedelta

import nltk
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, ReactionTypeEmoji, User
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt_tab')
nltk.download('stopwords')


def convert_to_mention(user: User):
    """Вытаскивает упоминание пользователя из объекта User"""
    return f'@{user.username}' if user.username else f'<a href="tg://user?id={user.id}">{user.full_name}</a>'


def is_spam(message: str) -> bool:
    """Проверяет, является ли сообщение спамом"""
    message = message.translate(str.maketrans('', '', string.punctuation))  # удаляем пунктуацию
    words = word_tokenize(message)  # токенизируем сообщение
    words = [word for word in words if word.lower() not in stopwords.words('russian')]  # удаляем стоп-слова

    if not words:
        return True
    if len(words) < 3:
        return True

    return False


router = Router()
ADMIN_CHAT = -1002367372290
START_MSG = '<b>Привет! 👋🏼 Это бот ITMO STUDENTS!</b>\n\nОбращайся к нам с идеями и предложениями, как сделать университет лучше, и проблемами, которые тебя волнуют. Мы от лица Актива ИТМО рассмотрим твою инициативу и постараемся реализовать её 🚀\n\nПросто отправь сообщение, и если бот поставил лайк, то мы получили твоё обращение — остаётся ждать ответ 🤓\n\n<b>Важно:</b> мы не отвечаем на вопросы, а инициируем предложения внутри университета.\nЗа ответами на вопросы обращайся ниже:\n✉️ <a href="https://helpdesk.itmo.ru/servicedesk/customer/portals">Центр поддержки</a>\n🤖 <a href="https://t.me/itmolnia_bot">ITMOLNIA BOT</a>\n👥 <a href="https://telegra.ph/Kontakty-po-rutinnym-voprosam-02-12">Контакты по рутинным вопросам</a>'
USERS_COOLDOWN: dict[int, datetime] = {}


@router.message(F.text.startswith('/start'))
async def start(msg: Message):
    await msg.answer(START_MSG)


@router.message(F.text, F.chat.type == 'private')
async def question(msg: Message):
    assert msg.from_user

    if msg.text and not msg.text.lower().startswith('полтергейст'):
        if is_spam(msg.text):
            return
        if (last_time := USERS_COOLDOWN.get(msg.from_user.id)) and datetime.now() < last_time + timedelta(minutes=5):
            await msg.react([ReactionTypeEmoji(emoji='🙊')])
            await msg.answer('Подождите 5 минут перед отправкой следующего сообщения! 📛')
            return

    await bot.send_message(
        ADMIN_CHAT,
        f'<b>Вопрос от {convert_to_mention(msg.from_user)}</b>\n\n{msg.html_text}\n\n<tg-spoiler>{msg.from_user.id} {msg.message_id}</tg-spoiler>',
    )
    USERS_COOLDOWN[msg.from_user.id] = datetime.now()

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    print(f'Question from {msg.from_user.id} {msg.message_id} sent to admin chat')


@router.message(Command('answer'), F.message_thread_id)
async def answer_question(msg: Message):
    assert msg.message_thread_id

    if msg.text == '/answer':
        await msg.react([ReactionTypeEmoji(emoji='💩')], True)
        return

    user_id, msg_id = map(int, msg.reply_to_message.text.rsplit('\n')[-1].split())
    await bot.send_message(user_id, msg.html_text.removeprefix('/answer '), reply_to_message_id=msg_id)

    if user_id in USERS_COOLDOWN:
        del USERS_COOLDOWN[user_id]

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    print(f'Answer to {user_id} {msg_id} sent')


bot = Bot(token='8124549178:AAGoWofJCCLacPiMxcNsPOZoKO0lmGPcJmQ', default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
dp.include_router(router)


async def main():
    await dp.start_polling(bot, handle_as_tasks=False, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
