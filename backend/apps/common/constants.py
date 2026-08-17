"""Перечисления и пределы общего приложения."""

from django.db import models

# Ник длиннее Telegram не даёт; строку браузера обрезаем сами, чтобы запись не пухла.
USERNAME_LENGTH = 32
USER_AGENT_LENGTH = 400
# SHA-256 в шестнадцатеричном виде — ровно 64 знака.
KEY_HASH_LENGTH = 64


class Source(models.TextChoices):
    """Откуда пришли. Ник и id есть только у пришедших через Telegram."""

    TELEGRAM = "telegram", "Telegram"
    SITE = "site", "Сайт"
