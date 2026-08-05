import pytest
from django.db.utils import IntegrityError

from apps.vocabulary.enums import Kind, Source
from apps.vocabulary.models import Entry

pytestmark = pytest.mark.django_db


def make_word(arabic: str, translation: str) -> Entry:
    return Entry.objects.create(
        kind=Kind.WORD, arabic=arabic, translation_ru=translation, source=Source.TEXTBOOK
    )


def test_save_fills_arabic_norm() -> None:
    assert make_word("كِتَاب", "книга").arabic_norm == "كتاب"


def test_exact_duplicate_is_rejected() -> None:
    make_word("كِتَاب", "книга")

    with pytest.raises(IntegrityError):
        make_word("كِتَاب", "книга")


def test_gender_pair_is_allowed() -> None:
    """Обе фразы дают один ключ нормализации, но уникальность стоит на точном
    арабском, поэтому женская форма должна сохраняться рядом с мужской.
    """
    masculine = Entry.objects.create(
        kind=Kind.PHRASE,
        arabic="مَا اسْمُكَ؟",
        translation_ru="как тебя зовут? (к мужчине)",
        source=Source.MANUAL,
    )
    feminine = Entry.objects.create(
        kind=Kind.PHRASE,
        arabic="مَا اسْمُكِ؟",
        translation_ru="как тебя зовут? (к женщине)",
        source=Source.MANUAL,
    )

    assert masculine.arabic_norm == feminine.arabic_norm
    assert Entry.objects.filter(kind=Kind.PHRASE).count() == 2


def test_same_skeleton_with_other_translation_is_allowed() -> None:
    make_word("عَيْن", "глаз")
    make_word("عَيْن", "источник")

    assert Entry.objects.count() == 2
