import asyncio
import string
from contextlib import suppress
from datetime import datetime
from functools import partial
from typing import Callable, TypedDict

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Filter
from aiogram.types import Message, User
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from config import ADMIN_CHAT, bot


def is_spam(message: str) -> bool:
    """Проверяет, является ли сообщение спамом"""
    message = message.translate(str.maketrans('', '', string.punctuation))  # удаляем пунктуацию
    words = word_tokenize(message, 'russian')  # токенизируем сообщение

    stop_words = stopwords.words('russian') + get_bad_words()  # объединяем стоп-слова и плохие слова
    words = list(filter(lambda word: word.lower() not in stop_words, words))  # удаляем стоп-слова

    if not words:
        return True
    if len(words) < 3:
        return True

    return False


def get_bad_words() -> list[str]:
    """Возвращает список плохих слов"""
    with open('bad_words.txt', 'r') as file:
        return [line.strip() for line in file.readlines() if line]


def save_unique_user(user_id: int):
    """Сохраняет уникального пользователя в файл"""
    with open('users.txt', 'a+') as file:
        if str(user_id) in file.read():
            return
        file.writelines([f'{user_id}'])


def get_unique_users() -> list[int]:
    """Возвращает список уникальных пользователей"""
    with open('users.txt', 'r') as file:
        return [int(line) for line in file.readlines()]


class AdminFilter(Filter):
    """Фильтр для проверки, является ли пользователь администратором бота (т.е. участником админ-канал)"""

    async def __call__(self, resp: Message):
        with suppress(TelegramBadRequest):
            await bot.get_chat_member(ADMIN_CHAT, resp.from_user.id)
            return True
        return False


def convert_to_mention(user: User):
    """Вытаскивает упоминание пользователя из объекта User"""
    return f'@{user.username}' if user.username else f'<a href="tg://user?id={user.id}">{user.full_name}</a>'


async def retry_func(func: Callable, *args, **kwargs):
    """Повторяет функцию, если бот натыкается на ошибку `TelegramRetryAfter`."""
    function = partial(func, *args, **kwargs)
    try:
        return await function()
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await function()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


class UserCooldown(TypedDict):
    last_time: datetime
    is_msg_sent: bool


class MailingDialog(TypedDict):
    user_id: int
    is_ready: bool
    msg_ids: list[int]
