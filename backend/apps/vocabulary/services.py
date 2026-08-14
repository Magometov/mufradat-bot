"""Правила колоды: что в неё ложится, что из неё берётся и как разбирают урок."""

from pathlib import Path

from django.core.files.base import File
from django.db import transaction
from django.db.models import QuerySet

from apps.vocabulary.constants import Theme
from apps.vocabulary.models import Phrase, Word, WordForm

# Единицы, которыми колоду разбирают: слово со всеми формами и отдельная фраза.
UNITS = {"word": Word, "phrase": Phrase}

Unit = Word | Phrase


class Occupied(Exception):
    """Место занято: такая карточка уже есть или у слова уже есть это число."""


def _attach(card: WordForm | Phrase, name: str, image: File | None) -> None:
    """Кладёт картинку под номером карточки: `w12.jpg` понятнее, чем `card_a1b2.jpg`."""
    if image is None:
        return

    card.image.save(f"{name}{card.pk}{Path(image.name or '').suffix or '.jpg'}", image, save=True)


def deck() -> list[WordForm | Phrase]:
    """Вся колода плоским списком: формы слов и фразы, свежие сверху."""
    forms = WordForm.objects.select_related("word").order_by(
        "-word__created_at", "-word_id", "number"
    )
    phrases = Phrase.objects.order_by("-created_at", "-id")

    return [*forms, *phrases]


def add_form(
    *,
    number: int,
    arabic: str,
    translation_ru: str,
    transliteration: str = "",
    image: File | None = None,
    word: Word | None = None,
) -> WordForm:
    """Кладёт форму в колоду. Без слова заводит новое — в разделе последнего урока."""
    if WordForm.objects.filter(arabic=arabic, translation_ru=translation_ru).exists():
        raise Occupied("уже в колоде")

    # Число у слова одно на форму: без проверки вторая такая же упала бы на ограничении.
    if word is not None and word.forms.filter(number=number).exists():
        raise Occupied("у слова уже есть это число")

    with transaction.atomic():
        if word is None:
            word = Word.objects.create(themes=[Theme.LAST_LESSON])

        # Картинка прикладывается после вставки: имя файла — номер карточки, а он
        # появляется только вместе со строкой.
        form = WordForm.objects.create(
            word=word,
            number=number,
            arabic=arabic,
            translation_ru=translation_ru,
            transliteration=transliteration,
        )
        _attach(form, "w", image)

        return form


def add_phrase(
    *,
    arabic: str,
    translation_ru: str,
    transliteration: str = "",
    image: File | None = None,
) -> Phrase:
    """Кладёт фразу в колоду — туда же, в раздел последнего урока."""
    if Phrase.objects.filter(arabic=arabic, translation_ru=translation_ru).exists():
        raise Occupied("уже в колоде")

    with transaction.atomic():
        phrase = Phrase.objects.create(
            themes=[Theme.LAST_LESSON],
            arabic=arabic,
            translation_ru=translation_ru,
            transliteration=transliteration,
        )
        _attach(phrase, "p", image)

        return phrase


def lesson_words() -> QuerySet[Word]:
    """Слова из раздела последнего урока — вместе с формами, они идут в подпись."""
    return Word.objects.filter(themes__contains=[Theme.LAST_LESSON]).prefetch_related("forms")


def lesson_phrases() -> QuerySet[Phrase]:
    """Фразы из раздела последнего урока."""
    return Phrase.objects.filter(themes__contains=[Theme.LAST_LESSON])


def move_targets() -> list[tuple[str, str]]:
    """Темы, по которым разбирают урок: сам раздел урока целью не бывает."""
    return [(theme.value, theme.label) for theme in Theme if theme != Theme.LAST_LESSON]


def move_from_lesson(unit: Unit, themes: list[str]) -> list[str]:
    """Выносит единицу из раздела урока в выбранные темы. Пустой список — без тем."""
    # Прочие темы остаются: разбор снимает только раздел урока.
    kept = [theme for theme in unit.themes if theme != Theme.LAST_LESSON]

    unit.themes = kept + [theme for theme in themes if theme not in kept]
    unit.save(update_fields=["themes"])

    return unit.themes
