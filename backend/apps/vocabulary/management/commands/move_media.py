"""Перенос картинок колоды с диска в бакет. Разовая команда: `make move-media`."""

from pathlib import Path

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.vocabulary.services import deck

# Через столько файлов команда отчитывается: перенос идёт минуты, молчать нельзя.
STEP = 50


class Command(BaseCommand):
    help = "Переносит картинки колоды в бакет. Имена файлов не меняются, база не трогается."

    def handle(self, *args: object, **options: object) -> None:
        if not settings.BUCKET_URL:
            raise CommandError("BUCKET_URL не задан — переносить некуда")

        moved, kept, lost = 0, 0, []

        for number, card in enumerate(deck(), start=1):
            if not card.image:
                continue

            name = card.image.name

            # Уже в бакете: команду можно запускать сколько угодно раз.
            if default_storage.exists(name):
                kept += 1
                continue

            source = Path(settings.MEDIA_ROOT) / name

            if not source.exists():
                lost.append(name)
                continue

            with source.open("rb") as picture:
                default_storage.save(name, File(picture))

            moved += 1

            if moved % STEP == 0:
                self.stdout.write(f"перенесено {moved}, просмотрено {number}")

        self.stdout.write(self.style.SUCCESS(f"готово: перенесено {moved}, уже было {kept}"))

        if lost:
            self.stdout.write(self.style.WARNING(f"нет файла на диске: {len(lost)}"))
            for name in lost:
                self.stdout.write(f"  {name}")
