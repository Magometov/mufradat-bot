"""Подписанная строка от клиента Telegram: сверка подписи и кто в ней."""

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from django.conf import settings


def user_from(init_data: str) -> tuple[int, str] | None:
    """id и ник из initData; None — если подписи нет, она не сошлась или в ней нет человека."""
    token = settings.BOT_TOKEN

    if not init_data or not token:
        return None

    # Пустые значения оставляем: Telegram считал подпись со всеми полями, что прислал.
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    signature = fields.pop("hash", "")

    if not signature or not _matches(fields, signature, token):
        return None

    return _user(fields.get("user", ""))


def _matches(fields: dict[str, str], signature: str, token: str) -> bool:
    """Сверяет подпись: HMAC по токену бота от полей, сложенных по алфавиту."""
    checked = "\n".join(f"{name}={value}" for name, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, checked.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, signature)


def _user(raw: str) -> tuple[int, str] | None:
    """Достаёт id и ник из поля `user`: в нём JSON. Не разобралось — писать нечего."""
    try:
        user = json.loads(raw)

        return int(user["id"]), str(user.get("username") or "")
    except (KeyError, TypeError, ValueError):
        return None
