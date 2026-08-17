"""Перечисления и пределы общего приложения."""

from datetime import timedelta

from django.db import models

# Ник длиннее Telegram не даёт; строку браузера обрезаем сами, чтобы запись не пухла.
USERNAME_LENGTH = 32
USER_AGENT_LENGTH = 400
# SHA-256 в шестнадцатеричном виде.
KEY_HASH_LENGTH = 64

# Столько живёт подпись Telegram: без срока перехваченная строка работает вечно.
SIGNATURE_MAX_AGE = timedelta(days=1)

# Поле, которое можно не заполнять.
BLANK_AND_NULL = {"blank": True, "null": True}


class Source(models.TextChoices):
    """Откуда пришли. Ник и id есть только у пришедших через Telegram."""

    TELEGRAM = "telegram", "Telegram"
    SITE = "site", "Сайт"
