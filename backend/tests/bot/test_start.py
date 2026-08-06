from dataclasses import dataclass, field
from typing import Any

from aiogram.types import MenuButtonDefault, MenuButtonWebApp

from apps.bot import texts
from apps.bot.handlers.start import handle_start
from apps.bot.keyboards import menu_button, open_app
from apps.bot.permissions import is_admin

APP_URL = "https://example.test/app"


@dataclass
class FakeUser:
    id: int
    username: str = "tester"


@dataclass
class FakeMessage:
    """Заглушка вместо aiogram-сообщения: хендлеру нужен только from_user и answer."""

    from_user: FakeUser
    answers: list[tuple[str, Any]] = field(default_factory=list)

    async def answer(self, text: str, reply_markup: Any = None) -> None:
        self.answers.append((text, reply_markup))


def test_admin_is_a_single_id(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = 795856546

    assert is_admin(795856546) is True
    assert is_admin(111) is False


def test_nobody_is_admin_when_id_is_unset(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = 0

    assert is_admin(0) is False


def test_open_app_button_absent_until_url_is_set(settings) -> None:
    settings.WEBAPP_URL = ""

    assert open_app() is None


def test_open_app_button_points_at_webapp(settings) -> None:
    settings.WEBAPP_URL = APP_URL

    keyboard = open_app()

    assert keyboard is not None
    assert keyboard.inline_keyboard[0][0].web_app.url == APP_URL


async def test_admin_gets_the_entry_format_and_both_prompt_buttons(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = 111
    message = FakeMessage(from_user=FakeUser(id=111))

    await handle_start(message)

    text, keyboard = message.answers[0]
    assert "بَيْت | дом" in text
    assert [button.text for button in keyboard.keyboard[0]] == [
        texts.AI_WORDS_BUTTON,
        texts.AI_PHRASES_BUTTON,
    ]


def test_menu_button_opens_the_app(settings) -> None:
    settings.WEBAPP_URL = APP_URL

    button = menu_button()

    assert isinstance(button, MenuButtonWebApp)
    assert button.web_app.url == APP_URL


def test_menu_button_falls_back_to_commands_without_url(settings) -> None:
    """Иначе на сброшенном адресе «Меню» осталось бы вести на мёртвую страницу."""
    settings.WEBAPP_URL = ""

    assert isinstance(menu_button(), MenuButtonDefault)


async def test_admin_also_gets_the_app_button(settings) -> None:
    """Админу кнопка из open_app не приходит, но колоду смотреть ему тоже нужно."""
    settings.ADMIN_TELEGRAM_ID = 111
    settings.WEBAPP_URL = APP_URL
    message = FakeMessage(from_user=FakeUser(id=111))

    await handle_start(message)

    _, keyboard = message.answers[0]
    app_button = keyboard.keyboard[1][0]
    assert app_button.text == texts.OPEN_APP_BUTTON
    assert app_button.web_app.url == APP_URL


async def test_admin_keyboard_is_only_prompts_without_url(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = 111
    settings.WEBAPP_URL = ""
    message = FakeMessage(from_user=FakeUser(id=111))

    await handle_start(message)

    _, keyboard = message.answers[0]
    assert len(keyboard.keyboard) == 1


async def test_user_is_invited_to_the_app(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = 111
    settings.WEBAPP_URL = APP_URL
    message = FakeMessage(from_user=FakeUser(id=222))

    await handle_start(message)

    text, keyboard = message.answers[0]
    assert texts.USER_WELCOME in text
    assert keyboard is not None


async def test_without_webapp_url_user_is_told_to_wait(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = 111
    settings.WEBAPP_URL = ""
    message = FakeMessage(from_user=FakeUser(id=444))

    await handle_start(message)

    text, keyboard = message.answers[0]
    assert texts.APP_NOT_READY in text
    assert keyboard is None
