import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, ReactionTypeEmoji
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def convert_to_mention(user):
    return f'@{user.username}' if user.username else f'<a href="tg://user?id={user.id}">{user.full_name}</a>'


router = Router()
ADMIN_CHAT = -1002367372290
START_MSG = '<b>Привет! 👋🏼 Это бот ITMO STUDENTS!</b>\n\nОбращайся к нам с идеями, предложениями и проблемами, которые тебя волнуют. Мы от лица Актива ИТМО рассмотрим твою инициативу и постараемся реализовать её! 🚀\n\nПросто отправь сообщение, и если бот поставил лайк, то мы получили твоё обращение — остаётся ждать ответ! 🤓\n\n<b>Важно:</b> мы не отвечаем на вопросы, а инициируем ваши предложения внутри университета. За ответами на вопросы обращайся ниже:\n✉️ <a href="https://helpdesk.itmo.ru/servicedesk/customer/portals">Центр поддержки</a>\n🤖 <a href="https://t.me/itmolnia_bot">ITMOLNIA BOT</a>\n👥 <a href="https://telegra.ph/Kontakty-po-rutinnym-voprosam-02-12">Контакты по рутинным вопросам</a>'
USERS_LAST_MESSAGE_TIME: dict[int, datetime] = {}


async def check_cooldown():
    for user_id in USERS_LAST_MESSAGE_TIME:
        if datetime.now() < USERS_LAST_MESSAGE_TIME[user_id] + timedelta(minutes=5):
            del USERS_LAST_MESSAGE_TIME[user_id]


@router.message(F.text.startswith('/start'))
async def start(msg: Message):
    await msg.answer(START_MSG)


@router.message(F.text, F.chat.type == 'private')
async def question(msg: Message):
    assert msg.text

    if len(msg.text) <= 10:
        return
    if msg.from_user.id in USERS_LAST_MESSAGE_TIME:
        await msg.answer('Подождите 5 минут перед отправкой следующего сообщения! 📛')
        return

    await bot.send_message(
        ADMIN_CHAT,
        f'<b>Вопрос от {convert_to_mention(msg.from_user)}</b>\n\n{msg.text}\n\n<tg-spoiler>{msg.from_user.id} {msg.message_id}</tg-spoiler>',
    )
    USERS_LAST_MESSAGE_TIME[msg.from_user.id] = datetime.now()

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    print(f'Question from {msg.from_user.id} {msg.message_id} sent to admin chat')


@router.message(Command('answer'), F.message_thread_id)
async def answer_question(msg: Message):
    assert msg.message_thread_id
    assert msg.text

    if msg.text == '/answer':
        await msg.react([ReactionTypeEmoji(emoji='💩')], True)
        return

    user_id, msg_id = map(int, msg.reply_to_message.text.rsplit('\n')[-1].split())
    await bot.send_message(user_id, msg.text.removeprefix('/answer '), reply_to_message_id=msg_id)

    if user_id in USERS_LAST_MESSAGE_TIME:
        del USERS_LAST_MESSAGE_TIME[user_id]

    await msg.react([ReactionTypeEmoji(emoji='👍')])
    print(f'Answer to {user_id} {msg_id} sent')


bot = Bot(token='8124549178:AAGoWofJCCLacPiMxcNsPOZoKO0lmGPcJmQ', default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
scheduler = AsyncIOScheduler()
dp.include_router(router)


async def main():
    scheduler.start()
    await dp.start_polling(bot, handle_as_tasks=False, allowed_updates=dp.resolve_used_update_types())


scheduler.add_job(check_cooldown, 'interval', seconds=10)
asyncio.run(main())
