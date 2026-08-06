from dataclasses import dataclass, field
from typing import Any

import pytest

from apps.bot import texts
from apps.bot.handlers.add import handle_text
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
    assert "Добавлено" in message.answers[0][0]


async def test_reversed_order_is_saved_the_same(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    await handle_text(admin_message("дом | بَيْت"))

    assert await Entry.objects.filter(arabic="بَيْت", translation_ru="дом").aexists()


async def test_multiword_arabic_is_the_same_kind_of_card(settings) -> None:
    """Фраза больше не отдельный тип — сохраняется так же, как одно слово."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    await handle_text(admin_message("مَا اسْمُكَ؟ | как тебя зовут? (к мужчине)"))

    assert await Entry.objects.filter(arabic="مَا اسْمُكَ؟").aexists()


async def test_duplicate_is_reported_not_saved_twice(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await handle_text(admin_message("بَيْت | дом"))

    message = admin_message("بَيْت | дом")
    await handle_text(message)

    assert "Уже есть" in message.answers[0][0]
    assert await Entry.objects.filter(arabic="بَيْت").acount() == 1


async def test_many_cards_in_one_message(settings) -> None:
    """Ответ ИИ — это список; вводить его по одной строке слишком долго."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("بَيْت | дом | bayt\nكِتَاب | книга\n\nقَلَم | ручка")
    await handle_text(message)

    assert await Entry.objects.acount() == 3
    # Пустая строка между карточками за карточку не считается.
    assert "Добавлено 3:" in message.answers[0][0]


async def test_added_cards_come_back_for_a_look(settings) -> None:
    """Огласовки проверяются глазами, поэтому отчёт возвращает сами карточки."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("بَيْت | дом\nكِتَاب | книга")
    await handle_text(message)

    answer = message.answers[0][0]
    assert "بَيْت" in answer
    assert "كِتَاب" in answer


async def test_one_broken_line_does_not_cancel_the_others(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("بَيْت | дом\nсовсем не карточка\nكِتَاب | книга")
    await handle_text(message)

    answer = message.answers[0][0]
    assert await Entry.objects.acount() == 2
    assert "Добавлено 2:" in answer
    assert "Не разобрал 1:" in answer
    # Непонятая строка возвращается целиком, чтобы её было видно.
    assert "совсем не карточка" in answer
    assert "Формат" in answer


async def test_duplicate_inside_one_message_is_counted_once(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("بَيْت | дом\nبَيْت | дом")
    await handle_text(message)

    answer = message.answers[0][0]
    assert await Entry.objects.acount() == 1
    assert "Добавлено 1:" in answer
    assert "Уже есть 1:" in answer


async def test_long_list_is_trimmed_but_says_how_much(settings) -> None:
    """Сообщение Telegram ограничено; молча терять хвост отчёта нельзя."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    count = texts.LIST_LIMIT + 5

    message = admin_message("\n".join(f"كلمة{number} | слово {number}" for number in range(count)))
    await handle_text(message)

    answer = message.answers[0][0]
    assert await Entry.objects.acount() == count
    assert f"Добавлено {count}:" in answer
    assert "и ещё 5" in answer


async def test_markup_in_a_line_cannot_break_the_answer(settings) -> None:
    """Отчёт уходит разметкой HTML, поэтому «<» из строки должен быть экранирован."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("بَيْت | дом <b>жирный</b>")
    await handle_text(message)

    assert "&lt;b&gt;" in message.answers[0][0]


async def test_broken_line_gets_the_format_back(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("просто текст без арабского")
    await handle_text(message)

    text = message.answers[0][0]
    assert "арабск" in text
    assert "Формат" in text
    assert not await Entry.objects.aexists()


async def test_blank_message_gets_the_format(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message("   \n\n  ")
    await handle_text(message)

    assert "Формат" in message.answers[0][0]
    assert not await Entry.objects.aexists()


async def test_non_admin_cannot_add(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = FakeMessage(text="بَيْت | дом", from_user=FakeUser(id=222))
    await handle_text(message)

    assert texts.ONLY_ADMIN_ADDS in message.answers[0][0]
    assert not await Entry.objects.aexists()
