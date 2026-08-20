"""Сообщение с карточкой: что уходит в чат."""

from dataclasses import replace

from bot.api import Reminder
from bot.reminders import _caption

CARD = Reminder(
    telegram_id=1,
    arabic="قَلَم",
    translation_ru="ручка",
    transliteration="qalam",
    image=None,
)


class TestReminderCaption:
    """Подпись карточки для чата: та же, что в группе, и без пустых строк."""

    def test_card_is_open(self):
        """Спойлера нет: карточка приходит открытой, как в группу."""
        text = _caption(CARD)

        assert text == "قَلَم\n\nручка\nqalam"

    def test_card_without_transliteration_has_no_empty_line(self):
        """Пустая транслитерация не оставляет за собой пустую строку."""
        assert _caption(replace(CARD, transliteration="")) == "قَلَم\n\nручка"

    def test_markup_characters_are_escaped(self):
        """«&» и «<» в словах не должны ломать разметку сообщения."""
        text = _caption(replace(CARD, translation_ru="сложно & просто", arabic="<нет>"))

        assert "&amp;" in text
        assert "&lt;нет&gt;" in text
