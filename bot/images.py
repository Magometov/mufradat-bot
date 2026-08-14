"""Картинки к карточкам: рисует FLUX.1 [schnell] через fal.ai."""

import asyncio
import base64
import logging

import httpx

from bot import config

logger = logging.getLogger(__name__)

API = "https://fal.run/fal-ai/flux/schnell"

# Общий стиль колоды: без него у каждой картинки свой фон и своя манера. `no text`
# не вкус, а починка — иначе модель подписывает рисунок исковерканными буквами.
STYLE = "cartoon illustration, plain background, no text"

# Квадрат: карточка показывает картинку в своей ширине, обрезать её нечем.
SIZE = "square_hd"

TIMEOUT = 120

# Сколько раз пробовать одну карточку и сколько ждать между попытками.
ATTEMPTS = 4
PAUSE = 3.0


class DrawFailed(Exception):
    """Картинка не вышла: причина словами в сообщении."""


def _request(prompt: str) -> dict[str, object]:
    """Что просим нарисовать. Стиль приклеивается к промпту владельца."""
    return {
        "prompt": f"{prompt}, {STYLE}",
        "image_size": SIZE,
        "num_images": 1,
        "output_format": "jpeg",
        # Картинка должна приехать в этом же ответе: второе соединение, до fal.media,
        # с российского хостинга рвётся, и оплаченная генерация уходит в мусор.
        "sync_mode": True,
    }


def _decode(url: str) -> bytes:
    """Достаёт файл из `data:`-ссылки — при sync_mode картинка лежит в ней самой."""
    head, _, payload = url.partition(",")

    if ";base64" not in head:
        raise DrawFailed(f"в ответе не base64, а {head[:40]}")

    return base64.b64decode(payload)


async def _fetch(url: str) -> bytes:
    """Качает картинку, если fal всё же ответил ссылкой: за неё уже заплачено."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url)

    if response.is_error:
        raise DrawFailed(f"картинка не скачалась: {response.status_code}")

    return response.content


async def _take(body: dict) -> bytes:
    """Вынимает единственную картинку из ответа."""
    images = body.get("images") or []

    if not images:
        raise DrawFailed("модель не вернула картинку")

    url = str(images[0].get("url", ""))

    return _decode(url) if url.startswith("data:") else await _fetch(url)


async def draw(prompt: str) -> bytes:
    """Рисует картинку по промпту. Повторяет только обрывы связи и пятисотые."""
    if not config.FAL_KEY:
        raise DrawFailed("нет FAL_KEY — рисовать нечем")

    headers = {"Authorization": f"Key {config.FAL_KEY}"}
    reason = "не вышло"

    for attempt in range(ATTEMPTS):
        if attempt:
            await asyncio.sleep(PAUSE)

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(API, json=_request(prompt), headers=headers)
        except httpx.HTTPError as error:
            # Обрыв на полпути — как раз то, из-за чего повторы и нужны.
            reason = f"связь с fal рвётся: {error}"
            logger.warning("попытка %s не удалась: %s", attempt + 1, error)
            continue

        # Ключ и деньги повторами не лечатся, только тратят время.
        if response.is_client_error:
            raise DrawFailed(f"fal отказал: {response.status_code} {response.text[:120]}")

        if response.is_error:
            reason = f"fal отвечает {response.status_code}"
            continue

        try:
            return await _take(response.json())
        except DrawFailed as error:
            reason = str(error)
        except ValueError as error:
            reason = f"ответ не разобрать: {error}"

    raise DrawFailed(reason)
