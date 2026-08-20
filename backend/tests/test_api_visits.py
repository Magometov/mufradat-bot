"""Ручка входов: предел частоты и связь с человеком."""

import pytest
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle

from apps.common.models import Visit

URL = "/api/v1/visits/"


@pytest.fixture
def tight_limit(monkeypatch) -> None:
    """Предел на два запроса: настоящие 60 в час гонять в тесте незачем."""
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"visits": "2/hour"})


@pytest.mark.django_db
class TestVisits:
    """Журнал входов: заход пишется, а частота ограничена."""

    def test_visit_is_logged(self, client, django_assert_num_queries):
        """Заход из приложения попадает в журнал."""
        with django_assert_num_queries(1):
            response = client.post(URL, {}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Visit.objects.count() == 1

    def test_too_many_visits_are_refused(self, client, tight_limit, django_assert_num_queries):
        """Журнал нельзя засорять сколько угодно: сверх предела ручка отвечает 429."""
        allowed = [client.post(URL, {}, format="json") for _ in range(2)]

        with django_assert_num_queries(0):
            refused = client.post(URL, {}, format="json")

        assert [answer.status_code for answer in allowed] == [status.HTTP_204_NO_CONTENT] * 2
        assert refused.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert Visit.objects.count() == 2
