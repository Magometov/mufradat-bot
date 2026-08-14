from collections import defaultdict
from typing import Any

from django.core.management.base import BaseCommand

from apps.vocabulary.cards import card_id
from apps.vocabulary.models import Number, WordForm
from apps.vocabulary.plurals import DRAFT_PAIRS

COLUMNS = (
    "слово",
    "число",
    "id",
    "арабское",
    "перевод",
    "транслитерация",
    "темы (справочно)",
    "картинка (справочно)",
)

SINGULAR = "ед"
PLURAL = "мн"


class Command(BaseCommand):
    """Выгружает слова таблицей для правки руками. Только читает базу.

    Номера в колонке «слово» уже расставлены: строки с одним номером станут одним
    словом. Пары взяты из черновика `plurals.DRAFT_PAIRS` — это предложение, решает
    вычитка. Фраз здесь нет: числа у фразы не бывает, сливать нечего.
    """

    help = "Выгрузить слова в TSV для правки: make dump > words.tsv"

    def handle(self, *args: Any, **options: Any) -> None:
        groups, proposed = _groups()
        lines = ["\t".join(COLUMNS)]

        for number, forms in enumerate(groups, start=1):
            for form in forms:
                is_plural = form.number == Number.PLURAL or form.pk in proposed
                lines.append(_row(str(number), PLURAL if is_plural else SINGULAR, form))

        self.stdout.write("\n".join(lines))


def _groups() -> tuple[list[list[WordForm]], set[int]]:
    """Строки, разложенные по будущим словам, и номера форм, ставших множественными.

    Начальные группы — нынешние слова: что уже слито, слитым и остаётся. Поверх них
    накладывается черновик пар, но только когда перевод в колоде один: «комната» это
    и حجرة, и غرفة, и предложить наугад значило бы увести форму под чужое слово.
    """
    forms = list(WordForm.objects.select_related("word"))
    groups: dict[int, list[WordForm]] = defaultdict(list)
    by_translation: dict[str, list[WordForm]] = defaultdict(list)

    for form in forms:
        groups[form.word_id].append(form)
        by_translation[form.translation_ru].append(form)

    proposed: set[int] = set()

    for singular, plural in DRAFT_PAIRS.items():
        ones = by_translation.get(singular, [])
        manys = by_translation.get(plural, [])

        if len(ones) != 1 or len(manys) != 1:
            continue

        one, many = ones[0], manys[0]
        if one.word_id == many.word_id or many.word_id not in groups:
            continue

        groups[one.word_id].extend(groups.pop(many.word_id))
        proposed.add(many.pk)

    ordered = [sorted(items, key=lambda form: _within(form, proposed)) for items in groups.values()]

    return sorted(ordered, key=lambda items: items[0].translation_ru), proposed


def _within(form: WordForm, proposed: set[int]) -> tuple[int, str]:
    """Внутри слова единственное идёт первым — по нему слово и узнаётся."""
    is_plural = form.number == Number.PLURAL or form.pk in proposed

    return (int(is_plural), form.translation_ru)


def _row(group: str, number: str, form: WordForm) -> str:
    return "\t".join(
        (
            group,
            number,
            card_id(form),
            form.arabic,
            form.translation_ru,
            form.transliteration,
            ",".join(form.word.themes),
            "есть" if form.image else "нет",
        )
    )
