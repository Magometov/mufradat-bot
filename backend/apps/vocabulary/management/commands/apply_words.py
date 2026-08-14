import sys
from argparse import ArgumentParser
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.vocabulary.cards import split_ids
from apps.vocabulary.management.commands.dump_words import PLURAL, SINGULAR
from apps.vocabulary.models import Number, Word, WordForm
from apps.vocabulary.themes import Theme

DELETE = "-"
NUMBERS = {SINGULAR: Number.SINGULAR, PLURAL: Number.PLURAL}
MIN_COLUMNS = 6


@dataclass(frozen=True)
class Row:
    """Строка файла: что делать с одной карточкой."""

    group: str
    number: int | None
    form_id: int
    arabic: str
    translation_ru: str
    transliteration: str


class Command(BaseCommand):
    """Применяет файл правки: склеивает слова, ставит числа, удаляет помеченное.

    Файл главнее базы, но только в своих границах: карточка, которой в нём нет, —
    признак того, что файл устарел, и команда отказывается работать целиком. Молча
    трогать то, чего вычитка не видела, нельзя.
    """

    help = "Применить правки из файла: make apply < words.tsv"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--file", help="Файл правки; по умолчанию читается со stdin")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, что изменилось бы, и ничего не менять",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        rows = _parse(_read(options["file"]))
        forms, sizes = _check(rows)

        # Помеченная на удаление строка, карточки которой уже нет, — это сделанная
        # работа, а не ошибка: иначе тот же файл нельзя было бы прогнать дважды.
        deleted = [row for row in rows if row.group == DELETE and row.form_id in forms]
        groups = list(_grouped(rows).values())
        changed = [group for group in groups if not _is_settled(group, forms, sizes)]
        retyped = [
            row for row in rows if row.group != DELETE and _is_retyped(row, forms[row.form_id])
        ]

        if not options["dry_run"]:
            _apply(deleted, changed, retyped, forms)

        # Останется столько, сколько строк не помечено на удаление, — независимо от
        # того, удаляются они этим прогоном или удалились прошлым.
        kept = sum(row.group != DELETE for row in rows)

        self._report(
            len(rows), kept, len(groups), deleted, changed, retyped, forms, options["dry_run"]
        )

    def _report(
        self,
        total: int,
        kept: int,
        groups: int,
        deleted: list[Row],
        changed: list[list[Row]],
        retyped: list[Row],
        forms: dict[int, WordForm],
        is_dry_run: bool,
    ) -> None:
        verb = "собралось бы" if is_dry_run else "собрано"
        self.stdout.write(f"Строк в файле: {total}, карточек останется: {kept}")
        self.stdout.write(f"Слов после правки: {groups}, из них {verb} заново: {len(changed)}")

        for group in changed:
            self.stdout.write("  " + " + ".join(forms[row.form_id].translation_ru for row in group))

        _block(self, "Удаляются", [f"w{row.form_id}  {forms[row.form_id]}" for row in deleted])
        _block(
            self,
            "Правится текст",
            [
                f"w{row.form_id}  {forms[row.form_id].translation_ru} → {row.translation_ru}"
                for row in retyped
            ],
        )


def _read(path: str | None) -> list[str]:
    if not path:
        return sys.stdin.read().splitlines()

    with open(path, encoding="utf-8") as file:
        return file.read().splitlines()


def _parse(lines: list[str]) -> list[Row]:
    """Разбирает файл. Первая строка — заголовок, колонки после шестой не читаются."""
    rows: list[Row] = []

    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) < MIN_COLUMNS:
            raise CommandError(f"строка {number}: колонок меньше {MIN_COLUMNS}")

        group, kind, card = (part.strip() for part in parts[:3])

        if group != DELETE and kind not in NUMBERS:
            raise CommandError(
                f"строка {number}: число «{kind}» — ожидаю «{SINGULAR}» или «{PLURAL}»"
            )

        rows.append(
            Row(
                group=group,
                number=None if group == DELETE else NUMBERS[kind],
                form_id=_form_id(card, number),
                arabic=parts[3].strip(),
                translation_ru=parts[4].strip(),
                transliteration=parts[5].strip(),
            )
        )

    return rows


def _form_id(card: str, line: int) -> int:
    """Номер формы из «w12». Фразы в этом файле не участвуют: числа у них нет."""
    try:
        forms, phrases = split_ids(card)
    except ValueError as error:
        raise CommandError(f"строка {line}: {error}") from error

    if phrases or len(forms) != 1:
        raise CommandError(f"строка {line}: «{card}» — ожидаю один номер формы вида w12")

    return forms[0]


def _check(rows: list[Row]) -> tuple[dict[int, WordForm], Counter[int]]:
    """Сверяет файл с базой до единой правки: полумеры здесь опаснее отказа."""
    if not rows:
        raise CommandError("файл пуст")

    if repeated := [pk for pk, count in Counter(row.form_id for row in rows).items() if count > 1]:
        listed = ", ".join(f"w{pk}" for pk in sorted(repeated))
        raise CommandError(f"в файле по два раза: {listed}")

    mentioned = {row.form_id for row in rows}
    forms = {
        form.pk: form for form in WordForm.objects.select_related("word").filter(pk__in=mentioned)
    }

    # Существовать обязаны только строки, которые остаются: удалённое во второй прогон
    # уже отсутствует, и требовать его на месте значило бы запретить повтор.
    kept = {row.form_id for row in rows if row.group != DELETE}
    if absent := kept - forms.keys():
        listed = ", ".join(f"w{pk}" for pk in sorted(absent))
        raise CommandError(f"в базе нет таких карточек: {listed}")

    if stale := set(WordForm.objects.values_list("pk", flat=True)) - mentioned:
        listed = ", ".join(f"w{pk}" for pk in sorted(stale))
        raise CommandError(f"файл устарел — в базе есть карточки, которых в нём нет: {listed}")

    for group, items in sorted(_grouped(rows).items()):
        if len(items) > len(NUMBERS):
            raise CommandError(f"слово «{group}»: форм больше {len(NUMBERS)}")
        if len({row.number for row in items}) != len(items):
            raise CommandError(f"слово «{group}»: два одинаковых числа")

    return forms, Counter(form.word_id for form in WordForm.objects.all())


def _grouped(rows: list[Row]) -> dict[str, list[Row]]:
    """Строки по будущим словам; помеченные на удаление в группы не попадают."""
    groups: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        if row.group != DELETE:
            groups[row.group].append(row)

    return groups


def _is_settled(group: list[Row], forms: dict[int, WordForm], sizes: Counter[int]) -> bool:
    """Слово уже собрано: те же формы у одного слова, и числа стоят как в файле."""
    words = {forms[row.form_id].word_id for row in group}
    if len(words) != 1 or sizes[words.pop()] != len(group):
        return False

    return all(forms[row.form_id].number == row.number for row in group)


def _is_retyped(row: Row, form: WordForm) -> bool:
    return (row.arabic, row.translation_ru, row.transliteration) != (
        form.arabic,
        form.translation_ru,
        form.transliteration,
    )


@transaction.atomic
def _apply(
    deleted: list[Row],
    changed: list[list[Row]],
    retyped: list[Row],
    forms: dict[int, WordForm],
) -> None:
    """Удаляет помеченное, пересобирает изменившиеся слова, правит текст.

    Слово собирается заново, а не переставляется по месту: одно число на слово база
    проверяет сразу, и перенос формы в занятое число упал бы на полпути. Пустое слово
    даёт чистое место, а прежние удаляются в конце, когда форм в них не осталось.

    Файл картинки при удалении карточки не трогается: удалить его надёжнее руками,
    чем потерять из-за опечатки в одной строке.
    """
    for row in deleted:
        forms[row.form_id].delete()

    for group in changed:
        sources = {forms[row.form_id].word for row in group}
        target = Word.objects.create(themes=_themes(sources))
        # `auto_now_add` чужую дату не принимает, а пересобранное слово не должно
        # прыгать в начало колоды.
        Word.objects.filter(pk=target.pk).update(
            created_at=min(word.created_at for word in sources)
        )

        for row in group:
            form = forms[row.form_id]
            form.word = target
            form.number = row.number
            form.save(update_fields=["word", "number"])

    for row in retyped:
        form = forms[row.form_id]
        form.arabic = row.arabic
        form.translation_ru = row.translation_ru
        form.transliteration = row.transliteration
        form.save(update_fields=["arabic", "translation_ru", "transliteration"])

    Word.objects.filter(forms__isnull=True).delete()


def _themes(words: set[Word]) -> list[str]:
    """Темы собранного слова — объединение по прежним, в порядке объявления `Theme`."""
    found: set[str] = set()
    for word in words:
        found.update(word.themes)

    return [theme for theme in Theme.values if theme in found]


def _block(command: BaseCommand, head: str, lines: list[str]) -> None:
    if not lines:
        return

    command.stdout.write(command.style.WARNING(f"\n{head}: {len(lines)}"))
    for line in lines:
        command.stdout.write(f"  {line}")
