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

# Разбор раздела урока. У темы к данным дописывается её код.
SORT_GO = "sort:go"
SORT_LATER = "sort:later"
SORT_THEME = "sort:theme:"
SORT_DONE = "sort:done"
SORT_NONE = "sort:none"

# Тем немного, но в столбик они выглядят списком, а не выбором.
THEMES_IN_ROW = 2

# Прогресс: переключатель напоминаний и подтверждение сброса.
REMINDERS_SWITCH = "reminders:switch"
RESET_GO = "reset:go"
RESET_KEEP = "reset:keep"


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


def sort() -> InlineKeyboardMarkup:
    """Разбирать ли остаток раздела сейчас: слова и фразы одного урока идут двумя
    заходами, и бот сам не отличит прошлый урок от первой половины этого."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Разобрать", callback_data=SORT_GO),
                InlineKeyboardButton(text="Позже", callback_data=SORT_LATER),
            ]
        ]
    )


def themes(available: list[tuple[str, str]], picked: list[str]) -> InlineKeyboardMarkup:
    """Темы галочками: нажатие ставит и снимает, «Готово» применяет отмеченные."""
    buttons = [
        InlineKeyboardButton(
            text=f"{'✓ ' if slug in picked else ''}{name}",
            callback_data=f"{SORT_THEME}{slug}",
        )
        for slug, name in available
    ]
    rows = [
        buttons[start : start + THEMES_IN_ROW] for start in range(0, len(buttons), THEMES_IN_ROW)
    ]
    rows.append(
        [
            InlineKeyboardButton(text="Готово", callback_data=SORT_DONE),
            InlineKeyboardButton(text="Оставить без темы", callback_data=SORT_NONE),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


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


def reminders(is_on: bool) -> InlineKeyboardMarkup:
    """Переключатель напоминаний. Кнопка тут к месту: это настройка, а не карточка."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Выключить" if is_on else "Включить",
                    callback_data=REMINDERS_SWITCH,
                )
            ]
        ]
    )


def reset() -> InlineKeyboardMarkup:
    """Подтверждение сброса: действие редкое и необратимое."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сбросить", callback_data=RESET_GO),
                InlineKeyboardButton(text="Отмена", callback_data=RESET_KEEP),
            ]
        ]
    )


def tips(*, private: bool) -> InlineKeyboardMarkup | None:
    """Кнопка в подсказки приложения. Без адреса приложения её нет.

    В беседе её нет тоже: кнопку приложения Telegram разрешает только в личном чате, а
    сообщение с ней отвергает целиком — с такой кнопкой `/help` в беседе молчал.
    """
    if not config.WEBAPP_URL or not private:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть подсказки",
                    web_app=WebAppInfo(url=f"{config.WEBAPP_URL}#tips"),
                )
            ]
        ]
    )
