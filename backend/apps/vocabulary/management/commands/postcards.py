"""Сборка карточек для чата разом: после правок рисования готовые файлы устаревают."""

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.vocabulary.services import deck, refresh_pictures, sweep_pictures
from apps.vocabulary.utils import shaped


class Command(BaseCommand):
    help = "Собрать карточки для чата. --again переписывает уже собранные."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--again",
            action="store_true",
            help="переписать уже собранные: рисование поменялось, а имена файлов те же",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        # Молча испортить всю колоду хуже, чем не собрать её вовсе.
        if not shaped():
            raise CommandError("Pillow собран без raqm: арабское на карточках выйдет ломаным")

        cards = deck()

        for card in cards:
            refresh_pictures(card, again=options["again"])

        swept = sweep_pictures(cards)

        self.stdout.write(f"карточек в колоде: {len(cards)}, убрано прежних: {swept}")
