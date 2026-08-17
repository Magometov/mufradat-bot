"""Сообщение с карточкой: что видно сразу, а что под спойлером."""

from dataclasses import replace

from bot.api import Reminder
from bot.reminders import _caption

CARD = Reminder(
    telegram_id=1,
    arabic="قَلَم",
    translation_ru="ручка",
    transliteration="qalam",
    image=None,
    is_first=False,
)


def test_answer_hides_under_spoiler():
    """Арабское видно, перевод и транслитерация закрыты: сначала вспоминаешь."""
    text = _caption(CARD)

    assert text.startswith("قَلَم")
    assert "<tg-spoiler>ручка\nqalam</tg-spoiler>" in text


def test_card_without_transliteration_has_no_empty_line():
    """Пустая транслитерация не оставляет за собой пустую строку."""
    text = _caption(replace(CARD, transliteration=""))

    assert "<tg-spoiler>ручка</tg-spoiler>" in text


def test_intro_and_hint_only_in_the_first_message():
    """Вступление и подсказка про выключение идут один раз."""
    first = _caption(replace(CARD, is_first=True))

    assert "раз в час с 9 до 21" in first
    assert "/reminders" in first

    assert "раз в час" not in _caption(CARD)
    assert "/reminders" not in _caption(CARD)


def test_markup_characters_are_escaped():
    """«&» и «<» в словах не должны ломать разметку сообщения."""
    text = _caption(replace(CARD, translation_ru="сложно & просто", arabic="<нет>"))

    assert "&amp;" in text
    assert "&lt;нет&gt;" in text
