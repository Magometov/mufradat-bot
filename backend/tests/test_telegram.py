"""Подпись Telegram: сверка и срок жизни."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.common.constants import SIGNATURE_MAX_AGE
from apps.common.utils import user_from

TOKEN = "12345:test-token"
USER = {"id": 42, "username": "ali"}

settings = override_settings(BOT_TOKEN=TOKEN)


def init_data(*, age: timedelta = timedelta(), user: dict | None = USER, token: str = TOKEN) -> str:
    """Собирает подписанную строку, как её присылает клиент Telegram."""
    signed_at = int((timezone.now() - age).timestamp())
    fields = {"auth_date": str(signed_at)}

    if user is not None:
        fields["user"] = json.dumps(user)

    checked = "\n".join(f"{name}={value}" for name, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, checked.encode(), hashlib.sha256).hexdigest()

    return urlencode(fields)


@settings
def test_fresh_signature_gives_the_user():
    assert user_from(init_data()) == (42, "ali")


@settings
def test_signature_older_than_a_day_is_refused():
    """Перехваченная строка не должна работать вечно."""
    assert user_from(init_data(age=SIGNATURE_MAX_AGE + timedelta(minutes=1))) is None


@settings
def test_signature_just_inside_the_window_still_works():
    assert user_from(init_data(age=SIGNATURE_MAX_AGE - timedelta(minutes=1))) is not None


@settings
def test_signature_from_the_future_is_refused():
    """Дата вперёд — признак подделки, а не спешащих часов клиента."""
    assert user_from(init_data(age=-timedelta(hours=2))) is None


@settings
def test_missing_date_is_refused():
    """Без `auth_date` срок не проверить, поэтому такой строке веры нет."""
    fields = {"user": json.dumps(USER)}
    checked = f"user={fields['user']}"
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, checked.encode(), hashlib.sha256).hexdigest()

    assert user_from(urlencode(fields)) is None


@settings
def test_broken_date_is_refused():
    """Нечитаемая дата — тоже отказ, а не падение."""
    fields = {"auth_date": "вчера", "user": json.dumps(USER)}
    checked = "\n".join(f"{name}={value}" for name, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, checked.encode(), hashlib.sha256).hexdigest()

    assert user_from(urlencode(fields)) is None


@settings
def test_foreign_signature_is_refused():
    """Строка, подписанная другим токеном, не проходит."""
    assert user_from(init_data(token="99999:other")) is None


@settings
def test_signature_without_user_gives_nothing():
    """Подпись сошлась, а человека в ней нет — писать нечего."""
    assert user_from(init_data(user=None)) is None


@override_settings(BOT_TOKEN="")
def test_without_token_nobody_is_recognised():
    """Без токена бота сверять нечем."""
    assert user_from(init_data()) is None


def test_epoch_dates_are_handled():
    """Ровно нулевая дата — старше суток, а не «сейчас»."""
    assert datetime.fromtimestamp(0, tz=UTC) < timezone.now() - SIGNATURE_MAX_AGE


@settings
@pytest.mark.parametrize("raw", ["", "hash=abc", "auth_date=1&hash=abc"])
def test_garbage_is_refused(raw):
    """Мусор вместо строки — отказ, а не исключение."""
    assert user_from(raw) is None
