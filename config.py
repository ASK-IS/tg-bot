import logging
from typing import TYPE_CHECKING

import nltk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

if TYPE_CHECKING:
    from utils import UserCooldown, MailingDialog

logging.basicConfig(
    format='[%(asctime)s] - %(levelname)s\t| %(message)s',
    force=True,
    level=logging.INFO,
    filename='logs.log',
    filemode='a',
)

START_MSG = '<b>Привет! 👋🏼 Это бот ITMO STUDENTS!</b>\n\nОбращайся к нам с идеями и предложениями, как сделать университет лучше, и проблемами, которые тебя волнуют. Мы от лица Актива ИТМО рассмотрим твою инициативу и постараемся реализовать её 🚀\n\nПросто отправь сообщение, и если бот поставил лайк, то мы получили твоё обращение — остаётся ждать ответ в течение нескольких дней 🤓\n\n<b>Важно:</b> мы не отвечаем на личные вопросы, а инициируем предложения внутри университета.\nЗа ответами на вопросы обращайся ниже:\n✉️ <a href="https://helpdesk.itmo.ru/servicedesk/customer/portals">Центр поддержки</a>\n🤖 <a href="https://t.me/itmolnia_bot">ITMOLNIA BOT</a>\n👥 <a href="https://telegra.ph/Kontakty-po-rutinnym-voprosam-02-12">Контакты по рутинным вопросам</a>'
WAIT5_MSG = 'Подождите 5 минут перед отправкой следующего сообщения! 📛'
NOEDITS_MSG = '⚠️ Отредактированные сообщения не дойдут до нас. Если ты хочешь исправить твоё прошлое сообщение, то затем отправь его ещё раз.'
Q_MSG = '<b>Вопрос от {}</b>\n\n{}\n\n<tg-spoiler>{} {}</tg-spoiler>\n#открыт'
MREADY_MSG = '<b>Запущен диалог рассылки!</b>\n\nОтправь сообщение, которое ты хочешь разослать, и напиши ещё раз /mailing.\nЕсли передумаешь, обязательно ещё раз отправь /mailing!\n\n⚠️ Кастомные эмодзи будут конвертированы в обычные!'
MALREADY_MSG = '⚠️ Диалог рассылки запущен другим пользователем!'

ADMIN_CHAT = -1002367372290
USERS_COOLDOWN: dict[int, 'UserCooldown'] = {}
MAILING_DIALOG: 'MailingDialog' = {'user_id': 0, 'is_ready': False, 'msg_ids': []}


nltk.download('punkt_tab')
nltk.download('stopwords')

bot = Bot(token='8124549178:AAGoWofJCCLacPiMxcNsPOZoKO0lmGPcJmQ', default=DefaultBotProperties(parse_mode='HTML'))
# bot = Bot(token='5101303789:AAHu9dlfAmzOSuY6zRtFCyQlncYX2RvPSck', default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
