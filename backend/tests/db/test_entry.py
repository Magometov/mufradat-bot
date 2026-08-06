import pytest
from django.db.utils import IntegrityError

from apps.vocabulary.models import Entry

pytestmark = pytest.mark.django_db


def make_word(arabic: str, translation: str) -> Entry:
    return Entry.objects.create(arabic=arabic, translation_ru=translation)


def test_exact_duplicate_is_rejected() -> None:
    make_word("كِتَاب", "книга")

    with pytest.raises(IntegrityError):
        make_word("كِتَاب", "книга")


def test_gender_pair_is_allowed() -> None:
    """Пара «к мужчине / к женщине» различается только последней харакой,
    и обе формы должны жить в базе отдельными карточками.
    """
    make_word("مَا اسْمُكَ؟", "как тебя зовут? (к мужчине)")
    make_word("مَا اسْمُكِ؟", "как тебя зовут? (к женщине)")

    assert Entry.objects.count() == 2


def test_same_word_with_other_translation_is_allowed() -> None:
    make_word("عَيْن", "глаз")
    make_word("عَيْن", "источник")

    assert Entry.objects.count() == 2
