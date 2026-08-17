"""Сообщение со словом для группы: карточка открыта целиком."""

from dataclasses import replace

from bot.api import GroupCard
from bot.group import _caption

CARD = GroupCard(
    chat_id=-1001,
    arabic="قَلَم",
    translation_ru="ручка",
    transliteration="qalam",
    image=None,
)


def test_the_card_is_open():
    """Спойлера нет: арабское, перевод и транслитерация видны сразу."""
    text = _caption(CARD)

    assert "tg-spoiler" not in text
    assert text == "قَلَم\n\nручка\nqalam"


def test_card_without_transliteration_has_no_empty_line():
    """Пустая транслитерация не оставляет за собой пустую строку."""
    assert _caption(replace(CARD, transliteration="")) == "قَلَم\n\nручка"


def test_markup_characters_are_escaped():
    """«&» и «<» в словах не должны ломать разметку сообщения."""
    text = _caption(replace(CARD, translation_ru="сложно & просто", arabic="<нет>"))

    assert "&amp;" in text
    assert "&lt;нет&gt;" in text
