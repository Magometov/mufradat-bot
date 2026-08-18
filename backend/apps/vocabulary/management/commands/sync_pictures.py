"""Картинки колоды в бакете: перенос с диска и сборка карточек для чата.

Команда для переезда, `make pictures`. Запускать можно сколько угодно раз: перенесённое
и собранное пропускается, поэтому она же чинит бакет, если из него что-то пропало.
"""

from pathlib import Path

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.vocabulary.services import deck, refresh_pictures

# Через столько карточек команда отчитывается: работа идёт минуты, молчать нельзя.
STEP = 50


class Command(BaseCommand):
    help = "Переносит картинки колоды в бакет и собирает карточки для чата."

    def handle(self, *args: object, **options: object) -> None:
        if not settings.BUCKET_ENABLED:
            raise CommandError("BUCKET_ENABLED выключен — переносить некуда")

        moved, lost = 0, []

        for number, card in enumerate(deck(), start=1):
            if not card.image:
                continue

            if not default_storage.exists(card.image.name):
                source = Path(settings.MEDIA_ROOT) / card.image.name

                if not source.exists():
                    lost.append(card.image.name)
                    continue

                with source.open("rb") as picture:
                    default_storage.save(card.image.name, File(picture))

                moved += 1

            refresh_pictures(card)

            if number % STEP == 0:
                self.stdout.write(f"просмотрено {number}, перенесено {moved}")

        self.stdout.write(self.style.SUCCESS(f"готово: перенесено {moved}"))

        if lost:
            self.stdout.write(self.style.WARNING(f"потеряно файлов: {len(lost)}"))

            for name in lost:
                self.stdout.write(f"  {name}")
