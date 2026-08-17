"""Ручка входов: предел частоты и связь с человеком."""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.common.models import Visit

URL = "/api/v1/visits/"


@pytest.fixture
def client() -> APIClient:
    # Пределы считаются в кэше, поэтому между тестами он чистится.
    cache.clear()

    return APIClient()


@pytest.fixture
def tight_limit(monkeypatch) -> None:
    """Предел на два запроса: настоящие 60 в час гонять в тесте незачем."""
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"visits": "2/hour"})


@pytest.mark.django_db
def test_visit_is_logged(client):
    assert client.post(URL, {}, format="json").status_code == 204
    assert Visit.objects.count() == 1


@pytest.mark.django_db
def test_too_many_visits_are_refused(client, tight_limit):
    """Журнал нельзя засорять сколько угодно: сверх предела ручка отвечает 429."""
    assert client.post(URL, {}, format="json").status_code == 204
    assert client.post(URL, {}, format="json").status_code == 204

    assert client.post(URL, {}, format="json").status_code == 429
    assert Visit.objects.count() == 2
