"""Ручка напоминаний: что бот забирает для чата и кого к ней пускают."""

from datetime import datetime

import pytest
from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.common.models import Learner
from apps.learning.constants import LEARNING
from apps.learning.models import CardState
from apps.vocabulary.services import postcard_url

URL = "/api/v1/internal/reminders/take/"

TOKEN = "bot-secret"
# Полдень по Москве — внутри окна, когда бот пишет; часы в настройках проекта московские.
NOON = make_aware(datetime(2026, 8, 17, 12, 0))


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
class TestRemindersTake:
    """Забор карточек для чата: по одной на человека, и только своим."""

    @pytest.fixture(autouse=True)
    def bot_at_noon(self, settings, monkeypatch) -> None:
        """Секрет бота и время: вне окна тишины выборка не зависела бы от часов машины."""
        settings.BOT_API_TOKEN = TOKEN
        settings.SCHEDULING_FOR_ALL = False
        monkeypatch.setattr(timezone, "now", lambda: NOON)

    def test_nothing_to_send_is_an_empty_list(self, client, django_assert_num_queries):
        """Некому писать — пустой список, а не пустая карточка."""
        with django_assert_num_queries(1):
            answer = client.post(URL, headers={HEADER: TOKEN})

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == []

    def test_struggling_card_goes_to_the_chat(self, client, form, django_assert_num_queries):
        """Карточка, которая не даётся, уезжает боту с адресатом и помечается отправленной."""
        learner = Learner.objects.create(telegram_id=555, username="ali", scheduling=True)
        state = CardState.objects.create(
            learner=learner, form=form, due_at=NOON, level=LEARNING, lapses=1
        )

        with django_assert_num_queries(5):
            answer = client.post(URL, headers={HEADER: TOKEN})

        state.refresh_from_db()

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == [
            {
                "telegram_id": 555,
                "arabic": form.arabic,
                "translation_ru": form.translation_ru,
                "transliteration": "",
                "image": postcard_url(form),
            }
        ]
        assert state.reminded_at == NOON

    def test_stranger_takes_nothing(self, client, django_assert_num_queries):
        """Без секрета ручка не отвечает: до выборки дело не доходит."""
        with django_assert_num_queries(0):
            answer = client.post(URL)

        assert answer.status_code == status.HTTP_403_FORBIDDEN
