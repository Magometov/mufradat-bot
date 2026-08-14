"""Обращения к бэкенду: колоду наполняет он, бот только просит."""

import httpx

from bot import config

TIMEOUT = 30

FORMS = "/api/v1/internal/forms/"
PHRASES = "/api/v1/internal/phrases/"


class Occupied(Exception):
    """Карточка не легла: место в колоде занято."""


class BackendError(Exception):
    """Бэкенд не ответил или ответил непонятным."""


def _reason(response: httpx.Response) -> str:
    """Причина отказа словами: бэкенд кладёт её в `detail`, а разбор полей — по полям."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200] or "пустой ответ"

    if isinstance(body, dict) and "detail" in body:
        return str(body["detail"])

    return str(body)


def _headers() -> dict[str, str]:
    """Заголовок с секретом. Не-латиница в токене — промах в настройках, а не в сети."""
    token = config.BOT_API_TOKEN or ""

    if not token.isascii():
        raise BackendError("в BOT_API_TOKEN не латиница — заголовок с таким не отправить")

    return {"X-Bot-Token": token}


async def _post(path: str, fields: dict[str, object], image: bytes | None = None) -> dict:
    """Шлёт запрос служебной ручке. Пустые поля не отправляет: у них есть значения по умолчанию."""
    payload = {name: value for name, value in fields.items() if value is not None}
    headers = _headers()
    # Картинка едет файлом в том же запросе: до согласия владельца она нигде не лежит.
    files = {"image": ("card.jpg", image, "image/jpeg")} if image else None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{config.BACKEND_URL}{path}", data=payload, files=files, headers=headers
            )
    except httpx.HTTPError as error:
        raise BackendError(f"не дозвонился до бэкенда: {error}") from error

    if response.status_code == httpx.codes.CONFLICT:
        raise Occupied(_reason(response))

    if response.is_error:
        raise BackendError(f"{response.status_code}: {_reason(response)}")

    return response.json()


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
    body = await _post(
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
    body = await _post(
        PHRASES,
        {
            "arabic": arabic,
            "translation_ru": translation_ru,
            "transliteration": transliteration,
        },
        image,
    )

    return int(body["phrase"])
