from dataclasses import dataclass, field
from typing import Any

import pytest

from apps.bot import texts
from apps.bot.handlers.prompt import handle_phrases, handle_words
from apps.bot.parsing import ParseError, parse_entry
from apps.bot.prompt import MESSAGE_LIMIT
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
    text: str = texts.AI_WORDS_BUTTON
    answers: list[str] = field(default_factory=list)

    async def answer(self, text: str, **_: Any) -> None:
        self.answers.append(text)


def admin_message() -> FakeMessage:
    return FakeMessage(from_user=FakeUser(id=ADMIN_ID))


async def test_words_prompt_lists_meanings_without_arabic(settings) -> None:
    """Списку нужно только «не повторяй», а по-русски он вчетверо короче."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")
    await Entry.objects.acreate(arabic="كِتَاب", translation_ru="книга")

    message = admin_message()
    await handle_words(message)

    prompt = message.answers[0]
    assert texts.meanings_block(2) in prompt
    assert "книга, дом" in prompt
    assert "بَيْت" not in prompt.split(texts.meanings_block(2))[1]


async def test_phrases_prompt_lists_meanings_without_arabic(settings) -> None:
    """Решение владельца: оба промпта показывают колоду переводами."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = admin_message()
    await handle_phrases(message)

    prompt = message.answers[0]
    assert texts.words_block(1) in prompt
    assert prompt.split(texts.words_block(1))[1].strip() == "дом"


async def test_phrases_prompt_names_the_pronouns(settings) -> None:
    """Местоимения карточками не заведены — иначе ИИ сочтёт их незнакомыми."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = admin_message()
    await handle_phrases(message)

    prompt = message.answers[0]
    assert "я, ты (муж.), ты (жен.), он, она, мы" in prompt


async def test_phrases_prompt_shows_no_sample_phrase(settings) -> None:
    """Какие фразы собирать, решает ИИ: образец сузил бы ему выбор."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = admin_message()
    await handle_phrases(message)

    prompt = message.answers[0]
    assert "Какие именно — решай сам" in prompt
    # Единственный арабский образец в промпте — про формат строки, и это слово, не фраза.
    assert prompt.count("بَيْت | дом | bayt") == 1
    assert "كِتَابِي" not in prompt


async def test_both_prompts_ask_for_the_bot_input_format(settings) -> None:
    """Ответ ИИ вставляется в бота как есть, поэтому формат должен приходить готовым."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    words, phrases = admin_message(), admin_message()
    await handle_words(words)
    await handle_phrases(phrases)

    for prompt in (words.answers[0], phrases.answers[0]):
        assert "арабское | перевод | транслитерация" in prompt
        assert "без нумерации и разметки" in prompt


async def test_phrases_prompt_forbids_new_words(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = admin_message()
    await handle_phrases(message)

    assert "Новых слов не вводи" in message.answers[0]


async def test_only_what_fits_a_telegram_message_is_sent(settings) -> None:
    """Сотня длинных записей в лимит не влезает; обрезаются самые старые."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.abulk_create(
        Entry(arabic=f"كلمة{number}", translation_ru=f"значение номер {number} " + "х" * 40)
        for number in range(100)
    )

    message = admin_message()
    await handle_phrases(message)

    prompt = message.answers[0]
    assert len(prompt) <= MESSAGE_LIMIT
    assert "значение номер 99" in prompt
    assert "значение номер 0 " not in prompt


async def test_prompt_says_how_many_cards_it_carries(settings) -> None:
    """Обрезать молча нельзя: иначе «последние 100» превращается в неизвестно что."""
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.abulk_create(
        Entry(arabic=f"كلمة{number}", translation_ru=f"значение номер {number} " + "х" * 40)
        for number in range(100)
    )

    message = admin_message()
    await handle_phrases(message)

    prompt = message.answers[0]
    listed = prompt.count("значение номер ")
    assert texts.words_block(listed) in prompt


async def test_empty_base_still_gets_a_prompt(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID

    words, phrases = admin_message(), admin_message()
    await handle_words(words)
    await handle_phrases(phrases)

    assert texts.AI_PROMPT_EMPTY in words.answers[0]
    assert texts.AI_PROMPT_EMPTY in phrases.answers[0]


async def test_non_admin_gets_no_prompt(settings) -> None:
    settings.ADMIN_TELEGRAM_ID = ADMIN_ID
    await Entry.objects.acreate(arabic="بَيْت", translation_ru="дом")

    message = FakeMessage(from_user=FakeUser(id=222))
    await handle_phrases(message)

    assert texts.ONLY_ADMIN_ADDS in message.answers[0]
    assert texts.words_block(1) not in message.answers[0]


@pytest.mark.parametrize("button", [texts.AI_WORDS_BUTTON, texts.AI_PHRASES_BUTTON])
def test_button_text_can_never_become_a_card(button: str) -> None:
    """Кнопка приходит обычным текстом. Если её перехват однажды сломается, она
    должна упереться в разбор, а не осесть в колоде карточкой.
    """
    with pytest.raises(ParseError):
        parse_entry(button)
