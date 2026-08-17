"""Обращения к бэкенду: колоду наполняет он, бот только просит."""

from dataclasses import dataclass

import httpx

from bot import config

TIMEOUT = 30

FORMS = "/api/v1/internal/forms/"
PHRASES = "/api/v1/internal/phrases/"
LESSON = "/api/v1/internal/lesson/"
MOVE = "/api/v1/internal/lesson/move/"
REMINDERS = "/api/v1/internal/reminders/take/"
SWITCH = "/api/v1/internal/reminders/switch/"
PROGRESS = "/api/v1/internal/progress/"
RESET = "/api/v1/internal/progress/reset/"
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
class Reminder:
    """Карточка для чата: кому и что отправить."""

    telegram_id: int
    arabic: str
    translation_ru: str
    transliteration: str
    image: str | None
    is_first: bool


@dataclass(frozen=True, slots=True)
class Progress:
    """Что у человека с прогрессом: этим бот отвечает на команды."""

    reminders_on: bool
    scheduling: bool
    cards: int


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


async def _send(method: str, path: str, **kwargs: object) -> dict | list:
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


async def reminders() -> list[Reminder]:
    """Спрашивает, кому что напомнить. Окно тишины и шаг решает бэкенд, не бот."""
    body = await _send("POST", REMINDERS)

    return [
        Reminder(
            telegram_id=int(card["telegram_id"]),
            arabic=card["arabic"],
            translation_ru=card["translation_ru"],
            transliteration=card["transliteration"],
            image=card["image"],
            is_first=bool(card["is_first"]),
        )
        for card in body
    ]


def _progress(body: dict) -> Progress:
    """Разбирает сводку по человеку."""
    return Progress(
        reminders_on=bool(body["reminders_on"]),
        scheduling=bool(body["scheduling"]),
        cards=int(body["cards"]),
    )


async def progress(*, telegram_id: int, username: str) -> Progress:
    """Спрашивает, что у человека с прогрессом."""
    body = await _send("POST", PROGRESS, json={"telegram_id": telegram_id, "username": username})

    return _progress(body)


async def switch_reminders(*, telegram_id: int, username: str) -> Progress:
    """Переворачивает признак напоминаний и отдаёт, каким он стал."""
    body = await _send("POST", SWITCH, json={"telegram_id": telegram_id, "username": username})

    return _progress(body)


async def reset_progress(*, telegram_id: int, username: str) -> Progress:
    """Обнуляет прогресс: колода остаётся, уходят уровни и сроки."""
    body = await _send("POST", RESET, json={"telegram_id": telegram_id, "username": username})

    return _progress(body)
