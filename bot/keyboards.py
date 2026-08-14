from aiogram.types import MenuButtonDefault, MenuButtonWebApp, WebAppInfo

from bot import config
from bot.texts import MENU_BUTTON


def menu_button() -> MenuButtonWebApp | MenuButtonDefault:
    """Синяя кнопка у поля ввода — вход в приложение, один на всех.

    Заглушку не учитывает: при работах приложение само отдаёт страницу о них.
    """
    if not config.WEBAPP_URL:
        return MenuButtonDefault()
    return MenuButtonWebApp(text=MENU_BUTTON, web_app=WebAppInfo(url=config.WEBAPP_URL))
