"""Разовая перерисовка колоды по плану: сначала черновики, потом перенос одобренных.

Команда временная — под правку картинок, найденных ревизией, и после неё удаляется
целиком вместе с каталогом `management`. Поэтому она нарочно ни на что не опирается:
обращение к fal и разбор номеров карточек повторены здесь, а не вынесены в общий код.
Так откат — это удаление файла, а не распутывание.
"""

import base64
import json
import time
import urllib.error
import urllib.request
from os import getenv
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from apps.vocabulary.models import Phrase, WordForm

# Номер карточки в плане тот же, что в приложении: `w12` — форма слова, `p3` — фраза.
KINDS = {"w": WordForm, "p": Phrase}

# Черновики лежат в media, поэтому Caddy отдаёт их как /m/drafts/<номер>.jpg и картинку
# видно, не заходя на сервер.
DRAFTS = "drafts"

API = "https://fal.run/fal-ai/flux/schnell"

# Стиль и размер списаны с bot/images.py: новые картинки должны встать в колоду
# незаметно, а не выделяться манерой.
STYLE = "cartoon illustration, plain background, no text"
SIZE = "square_hd"

TIMEOUT = 120
ATTEMPTS = 3
PAUSE = 3.0


class DrawFailed(Exception):
    """Картинка не вышла: причина словами в сообщении."""


def _decode(url: str) -> bytes:
    """Достаёт файл из `data:`-ссылки — при sync_mode картинка лежит в ней самой."""
    head, _, payload = url.partition(",")

    if ";base64" not in head:
        raise DrawFailed(f"в ответе не base64, а {head[:40]}")

    return base64.b64decode(payload)


def _fetch(url: str) -> bytes:
    """Качает картинку, если fal всё же ответил ссылкой: за неё уже заплачено."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return response.read()
    except urllib.error.URLError as error:
        raise DrawFailed(f"картинка не скачалась: {error}") from error


def _take(body: dict[str, Any]) -> bytes:
    """Вынимает единственную картинку из ответа."""
    images = body.get("images") or []

    if not images:
        raise DrawFailed("модель не вернула картинку")

    url = str(images[0].get("url", ""))

    return _decode(url) if url.startswith("data:") else _fetch(url)


def _ask(prompt: str, key: str) -> bytes:
    """Одна попытка: просит нарисовать и разбирает ответ."""
    request = urllib.request.Request(
        API,
        data=json.dumps(
            {
                "prompt": f"{prompt}, {STYLE}",
                "image_size": SIZE,
                "num_images": 1,
                "output_format": "jpeg",
                # Картинка должна приехать в этом же ответе: второе соединение, до
                # fal.media, с российского хостинга рвётся, и генерация уходит в мусор.
                "sync_mode": True,
            }
        ).encode(),
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return _take(json.load(response))
    except urllib.error.HTTPError as error:
        detail = error.read()[:120].decode(errors="replace")
        # Ключ и деньги повторами не лечатся, только тратят время.
        if error.code < 500:
            raise DrawFailed(f"fal отказал: {error.code} {detail}") from error
        raise DrawFailed(f"fal отвечает {error.code}") from error
    except urllib.error.URLError as error:
        raise DrawFailed(f"связь с fal рвётся: {error.reason}") from error
    except ValueError as error:
        raise DrawFailed(f"ответ не разобрать: {error}") from error


def draw(prompt: str, key: str) -> bytes:
    """Рисует картинку, повторяя обрывы связи и пятисотые."""
    reason = "не вышло"

    for attempt in range(ATTEMPTS):
        if attempt:
            time.sleep(PAUSE)

        try:
            return _ask(prompt, key)
        except DrawFailed as error:
            reason = str(error)
            # «fal отказал» — не про связь, повторять нечего.
            if reason.startswith("fal отказал"):
                raise

    raise DrawFailed(reason)


class Command(BaseCommand):
    help = "Перерисовать карточки по плану: черновики в media/drafts, затем --apply"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--plan",
            default="plans/words.json",
            help='JSON вида {"w12": "промпт"}',
        )
        parser.add_argument(
            "--only",
            nargs="+",
            default=[],
            metavar="НОМЕР",
            help='Ограничить набор: make redraw ONLY="w322 w324"',
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Не рисовать, а перенести готовые черновики в карточки",
        )

    def handle(self, *_: Any, **options: Any) -> None:
        plan = self._plan(Path(options["plan"]))
        chosen = self._chosen(plan, options["only"])
        drafts = Path(settings.MEDIA_ROOT) / DRAFTS
        drafts.mkdir(parents=True, exist_ok=True)

        if options["apply"]:
            self._apply(plan, chosen, drafts)
            return

        self._draw(plan, self._todo(chosen, drafts, options["only"]), drafts)

    def _plan(self, path: Path) -> dict[str, str]:
        """Читает план. Кривой план — остановка: рисовать наугад дороже, чем не рисовать."""
        if not path.exists():
            raise CommandError(f"плана нет: {path.resolve()}")

        try:
            plan = json.loads(path.read_text())
        except ValueError as error:
            raise CommandError(f"план не разобрать: {error}") from error

        if not isinstance(plan, dict) or not all(isinstance(v, str) and v for v in plan.values()):
            raise CommandError('план должен быть объектом вида {"w12": "промпт"}')

        unknown = [card_id for card_id in plan if card_id[:1] not in KINDS]
        if unknown:
            raise CommandError(f"непонятные номера в плане: {', '.join(unknown)}")

        return plan

    def _chosen(self, plan: dict[str, str], only: list[str]) -> list[str]:
        """Что берём в работу: весь план или названные номера."""
        if not only:
            return list(plan)

        missing = [card_id for card_id in only if card_id not in plan]
        if missing:
            raise CommandError(f"этих номеров в плане нет: {', '.join(missing)}")

        return only

    def _card(self, card_id: str) -> WordForm | Phrase | None:
        """Карточка по номеру из плана."""
        model = KINDS[card_id[:1]]
        number = card_id[1:]

        return model.objects.filter(pk=int(number)).first() if number.isdigit() else None

    def _todo(self, chosen: list[str], drafts: Path, only: list[str]) -> list[str]:
        """Готовые черновики второй раз не рисуются: обрыв прогона не должен стоить денег.

        Названные через `--only` — исключение: там как раз просят нарисовать заново.
        """
        if only:
            return chosen

        ready = [card_id for card_id in chosen if (drafts / f"{card_id}.jpg").exists()]

        if ready:
            self.stdout.write(f"уже нарисовано ранее: {len(ready)}, пропускаю")

        return [card_id for card_id in chosen if card_id not in set(ready)]

    def _draw(self, plan: dict[str, str], chosen: list[str], drafts: Path) -> None:
        """Рисует черновики. Карточки не трогает: до одобрения колода остаётся прежней."""
        if not chosen:
            self.stdout.write("рисовать нечего: черновики уже на месте")
            return

        key = getenv("FAL_KEY")
        if not key:
            raise CommandError("нет FAL_KEY — рисовать нечем")

        done, failed = [], []

        for position, card_id in enumerate(chosen, start=1):
            if self._card(card_id) is None:
                failed.append((card_id, "такой карточки нет в колоде"))
                self.stderr.write(f"{position}/{len(chosen)} {card_id}: нет в колоде")
                continue

            try:
                image = draw(plan[card_id], key)
            except DrawFailed as error:
                failed.append((card_id, str(error)))
                self.stderr.write(f"{position}/{len(chosen)} {card_id}: {error}")
                continue

            (drafts / f"{card_id}.jpg").write_bytes(image)
            done.append(card_id)
            self.stdout.write(f"{position}/{len(chosen)} {card_id}: готово")

        self.stdout.write("")
        self.stdout.write(f"нарисовано: {len(done)} из {len(chosen)}")
        self.stdout.write(f"смотреть: {settings.MEDIA_URL}{DRAFTS}/<номер>.jpg")

        if failed:
            self.stdout.write(f"не вышло: {len(failed)}")
            for card_id, reason in failed:
                self.stdout.write(f"  {card_id} — {reason}")
            self.stdout.write(f"повторить: --only {' '.join(card_id for card_id, _ in failed)}")

    def _apply(self, plan: dict[str, str], chosen: list[str], drafts: Path) -> None:
        """Переносит черновики в карточки. Перенесённый черновик удаляется, чтобы не лёг дважды."""
        applied, skipped = 0, []

        for card_id in chosen:
            draft = drafts / f"{card_id}.jpg"

            if not draft.exists():
                skipped.append((card_id, "черновика нет"))
                continue

            card = self._card(card_id)
            if card is None:
                skipped.append((card_id, "нет в колоде"))
                continue

            # Прежний файл удаляется, иначе media копит картинки, на которые никто не смотрит.
            if card.image:
                card.image.delete(save=False)

            card.image.save(f"{card_id}.jpg", ContentFile(draft.read_bytes()), save=True)
            draft.unlink()
            applied += 1
            self.stdout.write(f"{card_id}: в колоде")

        self.stdout.write("")
        self.stdout.write(f"перенесено: {applied} из {len(chosen)}")

        if skipped:
            self.stdout.write(f"пропущено: {len(skipped)}")
            for card_id, reason in skipped:
                self.stdout.write(f"  {card_id} — {reason}")
