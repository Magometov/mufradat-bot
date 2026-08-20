"""Заготовки для тестов ручек: клиент один на все файлы."""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture
def client() -> APIClient:
    """Клиент API с чистым кэшем: в кэше живёт счётчик ограничителя запросов."""
    cache.clear()

    return APIClient()
