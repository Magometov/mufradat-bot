from aiogram.types import MenuButtonDefault, MenuButtonWebApp, WebAppInfo
from django.conf import settings

from apps.bot.texts import MENU_BUTTON


def menu_button() -> MenuButtonWebApp | MenuButtonDefault:
    """Синяя кнопка рядом с полем ввода — единственный вход в приложение.

    Ставится один раз при запуске бота и действует у всех, и у админа, и у ученика.
    """
    # На время работ кнопка убирается: приложение как раз переезжает, и вести туда —
    # значит показать сломанную колоду вместо объяснения, что происходит.
    if not settings.WEBAPP_URL or settings.MAINTENANCE:
        return MenuButtonDefault()
    return MenuButtonWebApp(text=MENU_BUTTON, web_app=WebAppInfo(url=settings.WEBAPP_URL))
