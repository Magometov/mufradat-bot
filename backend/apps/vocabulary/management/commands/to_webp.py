"""Разовый перевод колоды в webp.

Команда временная: после прогона на сервере её удаляют вместе с этим пакетом.
Старые файлы она не трогает — они остаются на диске сиротами, и снимают их руками,
когда видно, что картинки на месте.
"""

from pathlib import Path
from typing import Any

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandParser

from apps.vocabulary import images
from apps.vocabulary.models import Phrase, WordForm

Card = WordForm | Phrase


def cards() -> list[Card]:
    """Все карточки с картинкой — формы слов и фразы вперемешку."""
    return [
        *WordForm.objects.exclude(image="").order_by("pk"),
        *Phrase.objects.exclude(image="").order_by("pk"),
    ]


def convert(card: Card) -> tuple[int, int, ContentFile]:
    """Пережимает картинку карточки, ничего не сохраняя: было, стало, новый файл."""
    before = card.image.size

    with card.image.open("rb") as source:
        content = images.to_webp(source)

    return before, content.size, content


class Command(BaseCommand):
    help = "Переводит картинки карточек в webp. Старые файлы остаются на диске."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="только показать, сколько выйдет, ничего не записывая",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry = options["dry_run"]
        before_total = after_total = 0
        done = skipped = failed = 0

        for card in cards():
            name = Path(card.image.name).name

            if Path(name).suffix.lower() == ".webp":
                skipped += 1
                continue

            try:
                before, after, content = convert(card)
            except (OSError, ValueError) as error:
                failed += 1
                self.stderr.write(f"{name}: не вышло — {error}")
                continue

            before_total += before
            after_total += after
            done += 1

            if not dry:
                card.image.save(f"{Path(name).stem}.webp", content, save=True)

            self.stdout.write(f"{name}: {_kb(before)} → {_kb(after)}")

        self._report(dry, done, skipped, failed, before_total, after_total)

    def _report(
        self,
        dry: bool,
        done: int,
        skipped: int,
        failed: int,
        before: int,
        after: int,
    ) -> None:
        """Итог прогона и что делать дальше."""
        verb = "перевелось бы" if dry else "переведено"
        self.stdout.write("")
        self.stdout.write(f"{verb}: {done}, уже webp: {skipped}, не вышло: {failed}")

        if done:
            self.stdout.write(f"всего: {_kb(before)} → {_kb(after)} ({before / after:.1f}x)")

        if dry or not done:
            return

        if failed:
            self.stdout.write("старые файлы не трогай, пока не разберёшься с ошибками выше")
            return

        self.stdout.write("старые файлы остались на диске; когда проверишь картинки, снеси их:")
        self.stdout.write("  find /app/media/cards -type f ! -name '*.webp' -delete")


def _kb(size: int) -> str:
    """Размер в килобайтах — байты для картинок не читаются."""
    return f"{size / 1024:.0f} КБ"
