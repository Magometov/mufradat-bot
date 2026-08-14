"""Настройки бота из окружения."""

import logging
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = int(getenv("ADMIN_TELEGRAM_ID") or 0)
WEBAPP_URL = getenv("WEBAPP_URL")
MAINTENANCE_FLAG = Path(getenv("MAINTENANCE_FLAG", "/flags/maintenance"))


def setup_logging() -> None:
    """Формат тот же, что у бэкенда."""
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} {levelname} {name}: {message}",
        style="{",
    )
