from aiogram.types import MenuButtonDefault, MenuButtonWebApp, WebAppInfo
from django.conf import settings

from apps.bot.texts import MENU_BUTTON


def menu_button() -> MenuButtonWebApp | MenuButtonDefault:
    """Синяя кнопка рядом с полем ввода — единственный вход в приложение.

    Ставится один раз при запуске бота и действует у всех, и у админа, и у ученика.
    """
    if not settings.WEBAPP_URL:
        return MenuButtonDefault()
    return MenuButtonWebApp(text=MENU_BUTTON, web_app=WebAppInfo(url=settings.WEBAPP_URL))
