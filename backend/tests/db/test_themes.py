import pytest
from django.core.exceptions import ValidationError

from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme

pytestmark = pytest.mark.django_db


def test_card_belongs_to_several_themes() -> None:
    """«Мой отец врач» — это и семья, и профессия: одной темы карточке мало."""
    entry = Entry.objects.create(
        arabic="وَالِدِي طَبِيبٌ",
        translation_ru="мой отец врач",
        themes=[Theme.FAMILY, Theme.NOUNS],
    )

    assert Entry.objects.get(pk=entry.pk).themes == ["family", "nouns"]


def test_themes_are_empty_by_default() -> None:
    """Бот и админка добавляют слово без темы — тему потом ставит скрипт или владелец."""
    entry = Entry.objects.create(arabic="بَيْت", translation_ru="дом")

    assert Entry.objects.get(pk=entry.pk).themes == []


def test_unknown_theme_is_rejected() -> None:
    entry = Entry(arabic="بَيْت", translation_ru="дом", themes=["животные"])

    with pytest.raises(ValidationError):
        entry.full_clean()


def test_theme_order_is_declaration_order() -> None:
    """Порядок кнопок на главной берётся отсюда, поэтому он часть контракта."""
    assert list(Theme.values) == [
        "numbers",
        "family",
        "greetings",
        "verbs",
        "antonyms",
        "nouns",
        "questions",
        "dialog3",
    ]


def test_lookup_finds_card_by_one_of_its_themes() -> None:
    Entry.objects.create(
        arabic="وَالِدِي طَبِيبٌ", translation_ru="мой отец врач", themes=[Theme.FAMILY, Theme.NOUNS]
    )
    Entry.objects.create(arabic="بَيْت", translation_ru="дом", themes=[Theme.NOUNS])

    found = Entry.objects.filter(themes__contains=[Theme.FAMILY])

    assert [entry.translation_ru for entry in found] == ["мой отец врач"]
