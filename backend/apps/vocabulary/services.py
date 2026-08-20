"""Правила колоды: что в неё ложится, что из неё берётся и как разбирают урок."""

from collections.abc import Iterable
from hashlib import sha1
from io import BytesIO

from django.core.files.base import ContentFile, File
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import QuerySet

from apps.vocabulary.constants import Theme
from apps.vocabulary.models import Phrase, Word, WordForm
from apps.vocabulary.utils import DRAWING_VERSION, card_id, parse, render, to_id, to_webp

# Единицы, которыми колоду разбирают: слово со всеми формами и отдельная фраза.
UNITS = {"word": Word, "phrase": Phrase}

Unit = Word | Phrase

Card = WordForm | Phrase

# Готовое для Telegram лежит рядом с колодой: собирается один раз и потом только читается.
READY = "telegram"

# Что готовим: собранную карточку. Слово попадает в имя файла.
POSTCARD = "card"


class Occupied(Exception):
    """Место занято: такая карточка уже есть или у слова уже есть это число."""


def _attach(card: Card, name: str, image: File | None) -> None:
    """Кладёт картинку под номером карточки: `w12.webp` понятнее, чем `card_a1b2.webp`."""
    if image is None:
        return

    card.image.save(f"{name}{card.pk}.webp", to_webp(image), save=True)


def forms() -> QuerySet[WordForm]:
    """Формы слов, свежие сверху; числа одного слова идут подряд."""
    return WordForm.objects.select_related("word").order_by(
        "-word__created_at", "-word_id", "number"
    )


def phrases() -> QuerySet[Phrase]:
    """Фразы, свежие сверху."""
    return Phrase.objects.order_by("-created_at", "-id")


def deck() -> list[Card]:
    """Вся колода плоским списком: формы слов и фразы, свежие сверху."""
    return [*forms(), *phrases()]


def find(query: str, *, limit: int) -> list[Card]:
    """Карточки по русскому слову. Пустой запрос — верх колоды.

    Ищем по переводу и подстрокой: колода своя, слов сотни, и «маш» должно находить
    машину. Потолок общий на слова и фразы, поэтому список не разрастается вдвое.
    """
    found_forms, found_phrases = forms(), phrases()

    if query:
        found_forms = found_forms.filter(translation_ru__icontains=query)
        found_phrases = found_phrases.filter(translation_ru__icontains=query)

    return [*found_forms[:limit], *found_phrases[:limit]][:limit]


def cards_by_id(card_ids: Iterable[str]) -> dict[str, Card]:
    """Карточки по номерам приложения. Неизвестные номера в ответ не попадают."""
    word_ids, phrase_ids = [], []

    for wanted in card_ids:
        parsed = parse(wanted)

        if parsed is None:
            continue

        is_word, pk = parsed
        (word_ids if is_word else phrase_ids).append(pk)

    found = {
        to_id(card.pk, is_word=True): card for card in WordForm.objects.filter(pk__in=word_ids)
    }
    found.update(
        {to_id(card.pk, is_word=False): card for card in Phrase.objects.filter(pk__in=phrase_ids)}
    )

    return found


def _ready(card: Card, kind: str) -> str:
    """Имя готового файла: номер карточки, версия рисования и слепок текста с картинкой.

    Всё, от чего карточка выглядит так, а не иначе, — в имени. Поменялось что-то одно,
    и адрес новый: по прежнему Telegram отдаёт ту картинку, которую скачал когда-то.
    """
    parts = (card.arabic, card.translation_ru, card.transliteration, card.image.name or "")
    stamp = sha1("|".join(parts).encode()).hexdigest()[:8]

    return f"{READY}/{kind}-{card_id(card)}-v{DRAWING_VERSION}-{stamp}.jpg"


def _drawn(card: Card) -> ContentFile:
    """Собранная карточка: слово, перевод, иллюстрация и транслитерация одной картинкой."""
    illustration = None

    if card.image:
        with card.image.open("rb") as source:
            illustration = BytesIO(source.read())

    return ContentFile(
        render(
            arabic=card.arabic,
            translation=card.translation_ru,
            transliteration=card.transliteration,
            illustration=illustration,
        )
    )


def refresh_pictures(card: Card, *, again: bool = False) -> None:
    """Готовит карточку для чата, если её ещё нет.

    Собирается и без иллюстрации: в чат такая карточка уезжает тем же способом, что
    остальные, только внутри картинки один текст.

    `again` — переписать готовую: пригодится, если файл побился, а имя ему причитается
    то же самое.
    """
    postcard = _ready(card, POSTCARD)

    if default_storage.exists(postcard):
        if not again:
            return

        default_storage.delete(postcard)

    default_storage.save(postcard, _drawn(card))


def sweep_pictures(cards: Iterable[Card]) -> int:
    """Убирает собранное, чего колода больше не ждёт, и говорит сколько убрала.

    Карточка сменила имя файла — прежний остался бы в бакете навсегда: его никто больше
    не спросит и никто не перепишет.
    """
    wanted = {_ready(card, POSTCARD) for card in cards}

    try:
        _, found = default_storage.listdir(READY)
    except FileNotFoundError:
        # Каталога ещё нет: ни одной карточки не собрано, убирать нечего.
        return 0

    stale = [f"{READY}/{name}" for name in found if f"{READY}/{name}" not in wanted]

    for name in stale:
        default_storage.delete(name)

    return len(stale)


def postcard_url(card: Card) -> str:
    """Адрес собранной карточки: она есть у каждой, даже у той, что без иллюстрации."""
    return default_storage.url(_ready(card, POSTCARD))


def known_cards(pairs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Какие из пар «арабское — перевод» уже лежат в колоде, в том же порядке.

    Спрашивается до записи: рисовать картинку тому, что уже есть, — впустую.
    """
    asked = list(pairs)
    arabic = {pair[0] for pair in asked}
    translations = {pair[1] for pair in asked}

    stored = set()
    for model in (WordForm, Phrase):
        stored.update(
            model.objects.filter(arabic__in=arabic, translation_ru__in=translations).values_list(
                "arabic", "translation_ru"
            )
        )

    return [pair for pair in asked if pair in stored]


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
        refresh_pictures(form)

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
        refresh_pictures(phrase)

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
