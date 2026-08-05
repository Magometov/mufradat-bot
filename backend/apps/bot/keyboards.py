from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from django.conf import settings

from apps.bot.texts import OPEN_APP_BUTTON


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
