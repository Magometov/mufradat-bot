import collections
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from apps.vocabulary.classification import themes_for
from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme


class Command(BaseCommand):
    """Расставляет темы по всей колоде правилами из `classification`."""

    help = "Расставить темы всем словам по их переводу"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать раскладку и ничего не записывать",
        )
        parser.add_argument(
            "--keep-manual",
            action="store_true",
            help="Не трогать слова, у которых темы уже стоят",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        entries = list(Entry.objects.order_by("pk"))
        changed: list[Entry] = []
        counts: collections.Counter[str] = collections.Counter()
        # Фраза, которой досталась только тема-остаток, — сигнал, что правила её
        # не разобрали. Существительным она может быть и по делу, поэтому не ошибка.
        fallback_only: list[Entry] = []

        for entry in entries:
            if options["keep_manual"] and entry.themes:
                counts.update(entry.themes)
                continue

            themes = themes_for(entry.translation_ru)
            counts.update(themes)

            if themes == [Theme.NOUNS] and " " in entry.arabic:
                fallback_only.append(entry)

            if themes != entry.themes:
                entry.themes = themes
                changed.append(entry)

        if not options["dry_run"] and changed:
            Entry.objects.bulk_update(changed, ["themes"], batch_size=500)

        self._report(len(entries), len(changed), counts, fallback_only, options["dry_run"])

    def _report(
        self,
        total: int,
        changed: int,
        counts: collections.Counter[str],
        fallback_only: list[Entry],
        is_dry_run: bool,
    ) -> None:
        verb = "изменилось бы" if is_dry_run else "изменено"
        self.stdout.write(f"Слов в базе: {total}, {verb}: {changed}")

        labels = dict(Theme.choices)
        for slug in Theme.values:
            self.stdout.write(f"  {labels[slug]:22} {counts[slug]}")

        if fallback_only:
            self.stdout.write(f"\nФраз только в «{labels[Theme.NOUNS]}»: {len(fallback_only)}")
            for entry in fallback_only[:20]:
                self.stdout.write(f"  {entry.pk}  {entry.translation_ru}")
            if len(fallback_only) > 20:
                self.stdout.write(f"  … и ещё {len(fallback_only) - 20}")
