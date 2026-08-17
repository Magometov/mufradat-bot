"""Помощники общего приложения: ни базы, ни запросов — чистые преобразования."""

from apps.common.utils.devices import device_name
from apps.common.utils.telegram import user_from

__all__ = ["device_name", "user_from"]
