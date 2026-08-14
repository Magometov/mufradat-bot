import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from os import getenv
from typing import Any

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.vocabulary.cards import card_id, split_ids
from apps.vocabulary.models import Phrase, WordForm
from apps.vocabulary.pictures import PROMPTS

# Карточка колоды: форма слова или фраза. Рисуются они одинаково — по переводу.
Card = WordForm | Phrase

API = "https://fal.run/fal-ai/flux/schnell"

# Квадрат: карточка показывает картинку в своей ширине, и обрезать её не хочется.
SIZE = "square_hd"

TIMEOUT = 120

# Сколько раз пробовать одну карточку и с какой паузой между попытками.
ATTEMPTS = 4
PAUSE = 3.0


def generate(prompt: str, key: str) -> str:
    """Просит нарисовать картинку по готовому промпту и отдаёт адрес файла."""
    body = json.dumps(
        {
            "prompt": prompt,
            "image_size": SIZE,
            "num_images": 1,
            "output_format": "jpeg",
            # Картинка приезжает прямо в этом ответе, а не ссылкой на CDN. Второе
            # соединение — до fal.media — с российского хостинга рвётся примерно
            # на каждой второй карточке, и оплаченная генерация уходила в мусор.
            "sync_mode": True,
        }
    ).encode()
    request = urllib.request.Request(
        API,
        data=body,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        images = json.load(response).get("images", [])

    if not images:
        raise ValueError("модель не вернула картинку")

    return images[0]["url"]


def download(url: str) -> bytes:
    """Достаёт файл: из `data:`-ссылки — прямо из ответа, иначе качает."""
    if url.startswith("data:"):
        head, _, payload = url.partition(",")
        if ";base64" not in head:
            raise ValueError(f"в ответе не base64, а {head}")
        return base64.b64decode(payload)

    request = urllib.request.Request(url, headers={"User-Agent": "mufradat-bot/0.1"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        kind = response.headers.get("Content-Type", "")
        if not kind.startswith("image/"):
            raise ValueError(f"это не картинка, а {kind or 'непонятно что'}")
        data = response.read()

    if not data:
        raise ValueError("пустой файл")

    return data


def draw(prompt: str, key: str) -> bytes:
    """Рисует картинку, повторяя попытку при сетевом обрыве.

    Повтор здесь не роскошь: соединение с российского хостинга до fal рвётся на
    полпути (`SSL: UNEXPECTED_EOF_WHILE_READING`), а брошенная попытка — это
    оплаченная генерация в мусор. Ошибки ключа и денег (4xx) не повторяем: они
    от повторов не лечатся, только тратят.
    """
    last: OSError | None = None

    for attempt in range(1, ATTEMPTS + 1):
        try:
            return download(generate(prompt, key))
        except urllib.error.HTTPError as error:
            if error.code < 500:
                raise
            last = error
        except OSError as error:
            last = error

        if attempt < ATTEMPTS:
            time.sleep(PAUSE * attempt)

    raise last if last else OSError("не удалось нарисовать")


class Command(BaseCommand):
    """Рисует карточкам картинки через FLUX.1 [schnell] по промптам из `pictures`."""

    help = "Нарисовать картинки словам из словаря pictures.PROMPTS"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--limit", type=int, help="Обработать не больше N карточек")
        parser.add_argument("--only", help="Только эти карточки: --only w12,p7")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Перерисовать и тем, у кого картинка уже есть",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать промпты и ничего не рисовать",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        key = getenv("FAL_KEY")
        if not key and not options["dry_run"]:
            raise CommandError("Нет FAL_KEY. Положи ключ fal.ai в .env — см. .env.example")

        cards = self._pick_cards(options)
        if not cards:
            self.stdout.write("Нечего рисовать.")
            return

        drawn = 0
        broken: list[tuple[Card, str]] = []

        for card in cards:
            prompt = PROMPTS[card.translation_ru]
            self.stdout.write(f"  {card_id(card):>5}  {card.translation_ru:34} {prompt}")

            if options["dry_run"]:
                continue

            try:
                data = draw(prompt, key)
            except urllib.error.HTTPError as error:
                if error.code in (401, 403):
                    raise CommandError(f"Ключ fal.ai не принят ({error.code})") from error
                broken.append((card, f"HTTP {error.code}"))
                continue
            except (OSError, ValueError, KeyError) as error:
                broken.append((card, str(error)))
                continue

            # Старый файл нужно убрать руками: Django не перезаписывает, а кладёт
            # рядом копию со случайным суффиксом, и том раздувается орфанами.
            if card.image:
                card.image.delete(save=False)

            card.image.save(f"{card_id(card)}.jpg", ContentFile(data), save=True)
            drawn += 1

        self._report(len(cards), drawn, broken, options["dry_run"])

    def _pick_cards(self, options: dict[str, Any]) -> list[Card]:
        """Карточки под рисование: и формы слов, и фразы — промпт ищется по переводу."""
        forms = WordForm.objects.filter(translation_ru__in=PROMPTS).order_by("pk")
        phrases = Phrase.objects.filter(translation_ru__in=PROMPTS).order_by("pk")

        if options["only"]:
            try:
                wanted_forms, wanted_phrases = split_ids(options["only"])
            except ValueError as error:
                raise CommandError(str(error)) from error
            forms = forms.filter(pk__in=wanted_forms)
            phrases = phrases.filter(pk__in=wanted_phrases)

        # Пропуск уже нарисованного делает команду возобновляемой: прогон можно
        # прервать на любой карточке и добрать остаток следующим запуском.
        if not options["replace"]:
            empty = Q(image="") | Q(image__isnull=True)
            forms = forms.filter(empty)
            phrases = phrases.filter(empty)

        cards: list[Card] = [*forms, *phrases]

        return cards[: options["limit"]] if options["limit"] else cards

    def _report(
        self,
        total: int,
        drawn: int,
        broken: list[tuple[Card, str]],
        is_dry_run: bool,
    ) -> None:
        self.stdout.write("")
        if is_dry_run:
            self.stdout.write(f"Промптов показано: {total}, ничего не нарисовано")
        else:
            self.stdout.write(f"Просмотрено: {total}, нарисовано: {drawn}")

        if broken:
            self.stdout.write(self.style.WARNING(f"Сорвалось: {len(broken)}"))
            for card, reason in broken:
                self.stdout.write(f"  {card_id(card)}  {card.translation_ru} — {reason}")
