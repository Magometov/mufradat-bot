import collections
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from apps.vocabulary.kind import is_word
from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme


class Command(BaseCommand):
    """Ставит галочку «Отдельное слово» по всей колоде правилом из `kind`."""

    help = "Отметить отдельные слова по всей колоде; прогон затирает правки из админки"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать раскладку и ничего не записывать",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        entries = list(Entry.objects.order_by("pk"))
        changed: list[Entry] = []
        words: collections.Counter[str] = collections.Counter()
        phrases: collections.Counter[str] = collections.Counter()
        marked = 0

        for entry in entries:
            is_single = is_word(entry.arabic, entry.translation_ru)
            marked += is_single
            (words if is_single else phrases).update(entry.themes)

            if is_single != entry.is_word:
                entry.is_word = is_single
                changed.append(entry)

        if not options["dry_run"] and changed:
            Entry.objects.bulk_update(changed, ["is_word"], batch_size=500)

        self._report(len(entries), marked, len(changed), words, phrases, options["dry_run"])

    def _report(
        self,
        total: int,
        marked: int,
        changed: int,
        words: collections.Counter[str],
        phrases: collections.Counter[str],
        is_dry_run: bool,
    ) -> None:
        verb = "изменилось бы" if is_dry_run else "изменено"
        self.stdout.write(f"Карточек в базе: {total}, {verb}: {changed}")
        self.stdout.write(f"Слов: {marked}, фраз: {total - marked}\n")

        labels = dict(Theme.choices)
        self.stdout.write(f"  {'':22} {'слов':>6} {'фраз':>6}")
        for slug in Theme.values:
            self.stdout.write(f"  {labels[slug]:22} {words[slug]:6} {phrases[slug]:6}")
