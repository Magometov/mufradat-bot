"""Обращения к бэкенду: колоду наполняет он, бот только просит."""

from dataclasses import dataclass

import httpx

from bot import config

TIMEOUT = 30

FORMS = "/api/v1/internal/forms/"
PHRASES = "/api/v1/internal/phrases/"
LESSON = "/api/v1/internal/lesson/"
MOVE = "/api/v1/internal/lesson/move/"
VISITS = "/api/v1/visits/"


class Occupied(Exception):
    """Карточка не легла: место в колоде занято."""


class BackendError(Exception):
    """Бэкенд не ответил или ответил непонятным."""


@dataclass(frozen=True, slots=True)
class Unit:
    """Единица разбора: слово со всеми формами или отдельная фраза."""

    kind: str
    id: int
    title: str


@dataclass(frozen=True, slots=True)
class Lesson:
    """Что лежит в разделе урока и по каким темам это можно разложить."""

    units: list[Unit]
    themes: list[tuple[str, str]]


def _headers() -> dict[str, str]:
    """Заголовок с секретом. Не-латиница в токене — промах в настройках, а не в сети."""
    token = config.BOT_API_TOKEN or ""

    if not token.isascii():
        raise BackendError("в BOT_API_TOKEN не латиница — заголовок с таким не отправить")

    return {"X-Bot-Token": token}


def _reason(response: httpx.Response) -> str:
    """Причина отказа словами: бэкенд кладёт её в `detail`, а разбор полей — по полям."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200] or "пустой ответ"

    if isinstance(body, dict) and "detail" in body:
        return str(body["detail"])

    return str(body)


async def _send(method: str, path: str, **kwargs: object) -> dict:
    """Зовёт служебную ручку и разбирает ответ."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(
                method, f"{config.BACKEND_URL}{path}", headers=_headers(), **kwargs
            )
    except httpx.HTTPError as error:
        raise BackendError(f"не дозвонился до бэкенда: {error}") from error

    if response.status_code == httpx.codes.CONFLICT:
        raise Occupied(_reason(response))

    if response.is_error:
        raise BackendError(f"{response.status_code}: {_reason(response)}")

    # Пустой ответ — это 204: ручке нечего сказать, кроме того, что она сделала своё.
    return response.json() if response.content else {}


async def _add(path: str, fields: dict[str, object], image: bytes | None) -> dict:
    """Добавляет карточку. Пустые поля не отправляет: у них есть значения по умолчанию."""
    return await _send(
        "POST",
        path,
        data={name: value for name, value in fields.items() if value is not None},
        # Картинка едет файлом в том же запросе: до согласия владельца она нигде не лежит.
        files={"image": ("card.jpg", image, "image/jpeg")} if image else None,
    )


async def add_form(
    *,
    number: int,
    arabic: str,
    translation_ru: str,
    transliteration: str,
    word: int | None = None,
    image: bytes | None = None,
) -> int:
    """Добавляет форму слова и отдаёт номер слова: им цепляется второе число."""
    body = await _add(
        FORMS,
        {
            "number": number,
            "arabic": arabic,
            "translation_ru": translation_ru,
            "transliteration": transliteration,
            "word": word,
        },
        image,
    )

    return int(body["word"])


async def add_phrase(
    *,
    arabic: str,
    translation_ru: str,
    transliteration: str,
    image: bytes | None = None,
) -> int:
    """Добавляет фразу и отдаёт её номер."""
    body = await _add(
        PHRASES,
        {
            "arabic": arabic,
            "translation_ru": translation_ru,
            "transliteration": transliteration,
        },
        image,
    )

    return int(body["phrase"])


async def log_visit(*, telegram_id: int, username: str) -> None:
    """Отмечает вход в журнал. Ручка та же, что у приложения: источник для нас один."""
    await _send("POST", VISITS, json={"telegram_id": telegram_id, "username": username})


async def lesson() -> Lesson:
    """Спрашивает, что осталось в разделе урока и куда это можно разложить."""
    body = await _send("GET", LESSON)

    return Lesson(
        units=[Unit(unit["kind"], int(unit["id"]), unit["title"]) for unit in body["units"]],
        themes=[(theme["slug"], theme["name"]) for theme in body["themes"]],
    )


async def move(*, kind: str, unit: int, themes: list[str]) -> None:
    """Выносит единицу из раздела урока. Пустой список тем — оставить без тем.

    Ходит JSON, а не формой: пустой список полем формы не передать вовсе.
    """
    await _send("POST", MOVE, json={"kind": kind, "id": unit, "themes": themes})
