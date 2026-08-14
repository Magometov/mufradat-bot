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
ADD_KEEP = "add:keep"
ADD_PLAIN = "add:plain"
ADD_REDRAW = "add:redraw"
ADD_EDIT = "add:edit"
ADD_DROP = "add:drop"


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
    """Согласие на разобранное. Оно же согласие на платные картинки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, рисуем", callback_data=ADD_GO),
                InlineKeyboardButton(text="Отмена", callback_data=ADD_CANCEL),
            ]
        ]
    )


def review() -> InlineKeyboardMarkup:
    """Приёмка карточки: что с ней делать. Из очереди выводит любая из кнопок."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить", callback_data=ADD_KEEP),
                InlineKeyboardButton(text="Без картинки", callback_data=ADD_PLAIN),
            ],
            [
                InlineKeyboardButton(text="Заменить изображение", callback_data=ADD_REDRAW),
                InlineKeyboardButton(text="Изменить", callback_data=ADD_EDIT),
            ],
            [InlineKeyboardButton(text="Не добавлять", callback_data=ADD_DROP)],
        ]
    )
