from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from django.conf import settings

from apps.bot.texts import AI_PHRASES_BUTTON, AI_WORDS_BUTTON, OPEN_APP_BUTTON


def admin_menu() -> ReplyKeyboardMarkup:
    """Клавиатура админа: промпты нужны несколько раз в неделю, пусть будут под рукой.

    Две кнопки в один ряд: расширить колоду новыми словами и закрепить имеющиеся
    фразами. Задачи разные, поэтому и промпты разные.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=AI_WORDS_BUTTON), KeyboardButton(text=AI_PHRASES_BUTTON)]],
        resize_keyboard=True,
    )


def open_app() -> InlineKeyboardMarkup | None:
    """Кнопка запуска Mini App; пока адрес не задан, кнопки нет."""
    if not settings.WEBAPP_URL:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=OPEN_APP_BUTTON, web_app=WebAppInfo(url=settings.WEBAPP_URL)
                )
            ]
        ]
    )
