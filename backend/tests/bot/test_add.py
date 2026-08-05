from dataclasses import dataclass, field
from typing import Any

import pytest

from apps.bot import texts
from apps.bot.handlers.add import handle_text
from apps.vocabulary.enums import Kind
from apps.vocabulary.models import Entry

# transaction=True обязателен: асинхронные запросы идут по своему соединению и не
# попадают в транзакцию, которую откатывает обычный django_db.
pytestmark = pytest.mark.django_db(transaction=True)

ADMIN_ID = 795856546


@dataclass
class FakeUser:
    id: int
    username: str = "tester"


@dataclass
class FakeMessage:
    text: str
    from_user: FakeUser
    answers: list[tuple[str, Any]] = field(default_factory=list)

    async def answer(self, text: str, reply_markup: Any = None) -> None:
        self.answers.append((text, reply_markup))


def admin_message(text: str) -> FakeMessage:
    return FakeMessage(text=text, from_user=FakeUser(id=ADMIN_ID))


async def test_word_is_saved(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("بَيْت | дом | bayt")
    await handle_text(message)

    entry = await Entry.objects.aget(arabic="بَيْت")
    assert entry.translation_ru == "дом"
    assert entry.transliteration == "bayt"
    assert entry.kind == Kind.WORD
    assert "Добавлено" in message.answers[0][0]


async def test_reversed_order_is_saved_the_same(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    await handle_text(admin_message("дом | بَيْت"))

    assert await Entry.objects.filter(arabic="بَيْت", translation_ru="дом").aexists()


async def test_phrase_keeps_its_kind(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    await handle_text(admin_message("مَا اسْمُكَ؟ | как тебя зовут? (к мужчине)"))

    entry = await Entry.objects.aget(translation_ru="как тебя зовут? (к мужчине)")
    assert entry.kind == Kind.PHRASE


async def test_duplicate_is_reported_not_saved_twice(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await handle_text(admin_message("بَيْت | дом"))

    message = admin_message("بَيْت | дом")
    await handle_text(message)

    assert "Уже есть" in message.answers[0][0]
    assert await Entry.objects.filter(arabic="بَيْت").acount() == 1


async def test_broken_line_gets_the_format_back(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("просто текст без арабского")
    await handle_text(message)

    text = message.answers[0][0]
    assert "арабск" in text
    assert "Формат" in text
    assert not await Entry.objects.aexists()


async def test_non_admin_cannot_add(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = FakeMessage(text="بَيْت | дом", from_user=FakeUser(id=222))
    await handle_text(message)

    assert texts.ONLY_ADMIN_ADDS in message.answers[0][0]
    assert not await Entry.objects.aexists()
