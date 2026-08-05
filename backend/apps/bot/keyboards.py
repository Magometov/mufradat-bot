from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from django.conf import settings

from apps.bot.texts import AI_PROMPT_BUTTON, OPEN_APP_BUTTON


def admin_menu() -> ReplyKeyboardMarkup:
    """Клавиатура админа: промпт нужен несколько раз в неделю, пусть будет под рукой."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=AI_PROMPT_BUTTON)]],
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
