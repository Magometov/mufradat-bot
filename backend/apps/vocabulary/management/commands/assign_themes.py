import collections
from argparse import ArgumentParser
from collections.abc import Callable, Iterable
from typing import Any

from django.core.management.base import BaseCommand

from apps.vocabulary.classification import themes_for
from apps.vocabulary.models import Phrase, Word
from apps.vocabulary.themes import Theme

DeckItem = Word | Phrase


class Command(BaseCommand):
    """Расставляет темы по всей колоде правилами из `classification`."""

    help = "Расставить темы словам и фразам по их переводу"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать раскладку и ничего не записывать",
        )
        parser.add_argument(
            "--keep-manual",
            action="store_true",
            help="Не трогать карточки, у которых темы уже стоят",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        counts: collections.Counter[str] = collections.Counter()
        words = list(Word.objects.prefetch_related("forms"))
        phrases = list(Phrase.objects.all())

        changed_words = self._assign(words, _word_themes, counts, options)
        changed_phrases = self._assign(phrases, _phrase_themes, counts, options)

        if not options["dry_run"]:
            Word.objects.bulk_update(changed_words, ["themes"], batch_size=500)
            Phrase.objects.bulk_update(changed_phrases, ["themes"], batch_size=500)

        # Фраза, которой досталась только тема-остаток, — сигнал, что правила её не
        # разобрали. Слову она может быть и по делу, поэтому смотрим только фразы.
        fallback_only = [phrase for phrase in phrases if phrase.themes == [Theme.NOUNS]]

        self._report(
            len(words),
            len(phrases),
            len(changed_words) + len(changed_phrases),
            counts,
            fallback_only,
            options["dry_run"],
        )

    def _assign(
        self,
        items: Iterable[DeckItem],
        themes_of: Callable[[Any], list[str]],
        counts: collections.Counter[str],
        options: dict[str, Any],
    ) -> list[DeckItem]:
        """Считает темы каждой карточке и собирает те, у которых они разошлись."""
        changed: list[DeckItem] = []

        for item in items:
            if options["keep_manual"] and item.themes:
                counts.update(item.themes)
                continue

            themes = themes_of(item)
            counts.update(themes)

            if themes != item.themes:
                item.themes = themes
                changed.append(item)

        return changed

    def _report(
        self,
        words: int,
        phrases: int,
        changed: int,
        counts: collections.Counter[str],
        fallback_only: list[Phrase],
        is_dry_run: bool,
    ) -> None:
        verb = "изменилось бы" if is_dry_run else "изменено"
        self.stdout.write(f"Слов: {words}, фраз: {phrases}, {verb}: {changed}")

        labels = dict(Theme.choices)
        for slug in Theme.values:
            self.stdout.write(f"  {labels[slug]:22} {counts[slug]}")

        if fallback_only:
            self.stdout.write(f"\nФраз только в «{labels[Theme.NOUNS]}»: {len(fallback_only)}")
            for phrase in fallback_only[:20]:
                self.stdout.write(f"  {phrase.pk}  {phrase.translation_ru}")
            if len(fallback_only) > 20:
                self.stdout.write(f"  … и ещё {len(fallback_only) - 20}")


def _word_themes(word: Word) -> list[str]:
    """Темы слова — объединение по всем его формам.

    Список третьего диалога перечисляет и «ванна», и «ванны»: объединение оставляет
    раздел на месте, какой бы формой он там ни был назван.
    """
    found: set[str] = set()
    for form in word.forms.all():
        found.update(themes_for(form.translation_ru))

    return [theme for theme in Theme.values if theme in found]


def _phrase_themes(phrase: Phrase) -> list[str]:
    return themes_for(phrase.translation_ru)
