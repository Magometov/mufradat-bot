from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonDefault,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from django.conf import settings

from apps.bot.texts import AI_PHRASES_BUTTON, AI_WORDS_BUTTON, MENU_BUTTON, OPEN_APP_BUTTON


def admin_menu() -> ReplyKeyboardMarkup:
    """Клавиатура админа: промпты нужны несколько раз в неделю, пусть будут под рукой.

    Две кнопки в один ряд: расширить колоду новыми словами и закрепить имеющиеся
    фразами. Задачи разные, поэтому и промпты разные.

    Вторым рядом — вход в приложение. Инлайновая кнопка из open_app админу никогда не
    приходит: /start для него заканчивается этой клавиатурой, — а колоду ему смотреть
    нужно так же, как ученику.
    """
    keyboard = [[KeyboardButton(text=AI_WORDS_BUTTON), KeyboardButton(text=AI_PHRASES_BUTTON)]]

    if settings.WEBAPP_URL:
        keyboard.append(
            [KeyboardButton(text=OPEN_APP_BUTTON, web_app=WebAppInfo(url=settings.WEBAPP_URL))]
        )

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def menu_button() -> MenuButtonWebApp | MenuButtonDefault:
    """Синяя кнопка рядом с полем ввода — постоянный вход в приложение.

    Кнопка в приветствии уезжает вверх по истории, а эта на месте всегда. Ставится
    один раз при запуске бота и действует у всех. Без адреса возвращается к списку
    команд, иначе «Меню» вело бы на мёртвую страницу.
    """
    if not settings.WEBAPP_URL:
        return MenuButtonDefault()
    return MenuButtonWebApp(text=MENU_BUTTON, web_app=WebAppInfo(url=settings.WEBAPP_URL))


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
