from dataclasses import dataclass, field
from typing import Any

import pytest

from apps.bot import texts
from apps.bot.handlers.prompt import handle_prompt
from apps.bot.parsing import ParseError, parse_entry
from apps.bot.prompt import MESSAGE_LIMIT
from apps.vocabulary.enums import Kind
from apps.vocabulary.models import Entry

pytestmark = pytest.mark.django_db(transaction=True)

ADMIN_ID = 795856546


@dataclass
class FakeUser:
    id: int
    username: str = "tester"


@dataclass
class FakeMessage:
    from_user: FakeUser
    text: str = texts.AI_PROMPT_BUTTON
    answers: list[str] = field(default_factory=list)

    async def answer(self, text: str, **_: Any) -> None:
        self.answers.append(text)


def admin_message() -> FakeMessage:
    return FakeMessage(from_user=FakeUser(id=ADMIN_ID))


async def test_prompt_carries_what_the_group_already_knows(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")
    await Entry.objects.acreate(
        kind=Kind.PHRASE,
        arabic="مَا اسْمُكَ؟",
        translation_ru="как тебя зовут?",
    )

    message = admin_message()
    await handle_prompt(message)

    prompt = message.answers[0]
    assert "بَيْت — дом" in prompt
    assert "مَا اسْمُكَ؟ — как тебя зовут?" in prompt


async def test_prompt_asks_for_the_bot_input_format(settings) -> None:
    """Ответ ИИ вводится руками по строке, поэтому строка должна приходить готовой."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = admin_message()
    await handle_prompt(message)

    assert "арабское | перевод | транслитерация" in message.answers[0]


async def test_only_what_fits_a_telegram_message_is_sent(settings) -> None:
    """Сотня длинных записей в лимит не влезает; обрезаются самые старые."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.abulk_create(
        Entry(arabic=f"كلمة{number}", translation_ru=f"слово номер {number} " + "х" * 40)
        for number in range(100)
    )

    message = admin_message()
    await handle_prompt(message)

    prompt = message.answers[0]
    assert len(prompt) <= MESSAGE_LIMIT
    assert "كلمة99 —" in prompt
    assert "كلمة0 —" not in prompt


async def test_prompt_says_how_many_words_it_carries(settings) -> None:
    """Обрезать молча нельзя: иначе «последние 100» превращается в неизвестно что."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.abulk_create(
        Entry(arabic=f"كلمة{number}", translation_ru=f"слово номер {number} " + "х" * 40)
        for number in range(100)
    )

    message = admin_message()
    await handle_prompt(message)

    prompt = message.answers[0]
    assert texts.words_block(prompt.count(" — слово номер ")) in prompt


async def test_empty_base_still_gets_a_prompt(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    message = admin_message()
    await handle_prompt(message)

    assert texts.AI_PROMPT_EMPTY in message.answers[0]


async def test_non_admin_gets_no_prompt(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = FakeMessage(from_user=FakeUser(id=222))
    await handle_prompt(message)

    assert texts.ONLY_ADMIN_ADDS in message.answers[0]
    assert "بَيْت — дом" not in message.answers[0]


def test_button_text_can_never_become_a_card() -> None:
    """Кнопка приходит обычным текстом. Если её перехват однажды сломается, она
    должна упереться в разбор, а не осесть в колоде карточкой.
    """
    with pytest.raises(ParseError):
        parse_entry(texts.AI_PROMPT_BUTTON)
