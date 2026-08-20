"""Служебные ручки прогресса и напоминаний: что они отдают боту и кого пускают."""

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.common.models import Learner
from apps.learning.models import CardState
from apps.vocabulary.models import WordForm

PROGRESS = "/api/v1/internal/progress/"
RESET = "/api/v1/internal/progress/reset/"
SWITCH = "/api/v1/internal/reminders/switch/"

TOKEN = "bot-secret"


def ask(client: APIClient, url: str, *, telegram_id: int = 777, token: str = TOKEN):
    """Запрос от бота: кто спрашивает — в теле, общий секрет — в заголовке."""
    headers = {HEADER: token} if token else {}

    return client.post(
        url, {"telegram_id": telegram_id, "username": "ann"}, format="json", headers=headers
    )


@pytest.mark.django_db
class TestProgress:
    """Сводка по человеку: заводит его сама, считает оценённое и переключает напоминания."""

    @pytest.fixture(autouse=True)
    def bot_settings(self, settings) -> None:
        """Секрет и общее расписание задаёт тест: от окружения сводка зависеть не должна."""
        settings.BOT_API_TOKEN = TOKEN
        settings.SCHEDULING_FOR_ALL = False

    def test_progress_of_unknown_learner_starts_him_empty(self, client, django_assert_num_queries):
        """Команда бота может прийти раньше первого захода: человек заводится на месте."""
        with django_assert_num_queries(5):
            answer = ask(client, PROGRESS)

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {"reminders_on": True, "scheduling": False, "cards": 0}
        assert Learner.objects.get().telegram_id == 777

    def test_progress_counts_answered_cards(self, client, learner, form, django_assert_num_queries):
        """В сводке — сколько карточек человек оценивал, а не сколько их в колоде."""
        CardState.objects.create(learner=learner, form=form, due_at=timezone.now())

        with django_assert_num_queries(3):
            answer = ask(client, PROGRESS, telegram_id=learner.telegram_id)

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json()["cards"] == 1

    def test_reset_forgets_the_levels_and_keeps_the_deck(
        self, client, learner, form, django_assert_num_queries
    ):
        """Обнуление уносит состояния карточек, но не сами карточки."""
        CardState.objects.create(learner=learner, form=form, due_at=timezone.now())

        with django_assert_num_queries(4):
            answer = ask(client, RESET, telegram_id=learner.telegram_id)

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json()["cards"] == 0
        assert CardState.objects.count() == 0
        assert WordForm.objects.filter(pk=form.pk).exists()

    def test_switch_flips_reminders_and_answers_the_summary(
        self, client, learner, django_assert_num_queries
    ):
        """Ручка переворачивает признак сама: боту не надо знать текущее состояние."""
        with django_assert_num_queries(4):
            answer = ask(client, SWITCH, telegram_id=learner.telegram_id)

        learner.refresh_from_db()

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {"reminders_on": False, "scheduling": False, "cards": 0}
        assert learner.reminders_on is False

    @pytest.mark.parametrize("url", [PROGRESS, RESET, SWITCH])
    def test_stranger_is_refused_everywhere(self, client, url, django_assert_num_queries):
        """Служебные ручки наружу не выпускаются: без секрета до базы дело не доходит."""
        with django_assert_num_queries(0):
            answer = ask(client, url, token="")

        assert answer.status_code == status.HTTP_403_FORBIDDEN
