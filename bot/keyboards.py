from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonDefault,
    MenuButtonWebApp,
    WebAppInfo,
)

from bot import config
from bot.texts import MENU_BUTTON

# Данные кнопок добавления. Вынесены в константы: их сверяют обработчики, а опечатку
# в строке ничем не поймать — кнопка просто перестанет отвечать.
ADD_WORDS = "add:words"
ADD_PHRASES = "add:phrases"
ADD_GO = "add:go"
ADD_CANCEL = "add:cancel"


def menu_button() -> MenuButtonWebApp | MenuButtonDefault:
    """Синяя кнопка у поля ввода — вход в приложение, один на всех.

    Заглушку не учитывает: при работах приложение само отдаёт страницу о них.
    """
    if not config.WEBAPP_URL:
        return MenuButtonDefault()
    return MenuButtonWebApp(text=MENU_BUTTON, web_app=WebAppInfo(url=config.WEBAPP_URL))


def pick() -> InlineKeyboardMarkup:
    """Что добавляем: с этого начинается любое добавление."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить слова", callback_data=ADD_WORDS),
                InlineKeyboardButton(text="Добавить фразы", callback_data=ADD_PHRASES),
            ]
        ]
    )


def cancel() -> InlineKeyboardMarkup:
    """Висит под форматом: из ожидания строк должен быть выход, а не только вставка."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=ADD_CANCEL)]]
    )


def confirm() -> InlineKeyboardMarkup:
    """Согласие на запись разобранного."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, добавить", callback_data=ADD_GO),
                InlineKeyboardButton(text="Отмена", callback_data=ADD_CANCEL),
            ]
        ]
    )
