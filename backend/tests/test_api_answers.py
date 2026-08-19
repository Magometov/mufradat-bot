"""Ручка оценок: пачка, время нажатия, пределы и кто её вправе присылать."""

from datetime import UTC, datetime, timedelta

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.common.constants import INIT_DATA_HEADER
from apps.common.models import Learner
from apps.learning.models import CardState
from tests.test_telegram import TOKEN, init_data

URL = "/api/v1/answers/"
# Время нажатия: тесты задают его сами, чтобы срок не зависел от часов машины.
PRESSED = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)

signature = override_settings(
    BOT_TOKEN=TOKEN, LADDER=[1, 2, 3, 4, 5], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=3, SIDES_NEEDED=2
)


@pytest.fixture
def client() -> APIClient:
    """Клиент с чистым кэшем: в нём живёт счётчик ограничителя запросов."""
    cache.clear()

    return APIClient()


def answer(card_id: str, verdict: str, *, at: datetime = PRESSED) -> dict:
    """Оценка, какой её присылает приложение: с временем нажатия."""
    return {"card_id": card_id, "verdict": verdict, "answered_at": at.isoformat()}


def send(client: APIClient, answers: list[dict], *, signed: bool = True):
    """Отправляет пачку оценок. Без подписи — от неопознанного."""
    headers = {INIT_DATA_HEADER: init_data()} if signed else {}

    return client.post(URL, {"answers": answers}, format="json", headers=headers)


@pytest.mark.django_db
class TestAnswers:
    """Оценка доезжает до базы: уровень, срок от нажатия и защита от повторов."""

    @signature
    def test_answer_is_applied_and_returned(self, client, form, django_assert_num_queries):
        """Оценка записывается, а в ответ едет новое состояние карточки."""
        with django_assert_num_queries(9):
            sent = send(client, [answer(f"w{form.pk}", "know")])

        assert sent.status_code == status.HTTP_200_OK

        state = CardState.objects.get()
        card = sent.json()[0]

        assert (card["id"], card["level"], card["step"]) == (f"w{form.pk}", 0, 1)
        assert parse_datetime(card["due_at"]) == state.due_at

    @signature
    def test_batch_is_applied_in_order(self, client, form, django_assert_num_queries):
        """Пачка применяется по порядку: вторая сторона закрывает карточку."""
        card_id = f"w{form.pk}"

        with django_assert_num_queries(11):
            sent = send(
                client,
                [
                    answer(card_id, "know"),
                    answer(card_id, "know", at=PRESSED + timedelta(seconds=20)),
                ],
            )

        assert [(state["level"], state["step"]) for state in sent.json()] == [(0, 1), (3, 0)]
        assert CardState.objects.get().level == 3

    @signature
    def test_due_counts_from_the_moment_of_the_press(self, client, form, django_assert_num_queries):
        """Срок считается от времени нажатия, а не от того, когда пачка доехала."""
        card_id = f"w{form.pk}"
        closed = PRESSED + timedelta(seconds=20)

        with django_assert_num_queries(11):
            sent = send(client, [answer(card_id, "know"), answer(card_id, "know", at=closed)])

        # Лестница без разброса, третий уровень — три дня от нажатия, закрывшего карточку.
        assert parse_datetime(sent.json()[1]["due_at"]) == closed + timedelta(days=3)
        assert CardState.objects.get().answered_at == closed

    @signature
    def test_repeated_batch_changes_nothing(self, client, form, django_assert_num_queries):
        """Та же пачка, присланная снова, уровень не двигает: ответ мог потеряться в дороге."""
        answers = [answer(f"w{form.pk}", "know")]
        send(client, answers)

        with django_assert_num_queries(5):
            again = send(client, answers)

        assert again.status_code == status.HTTP_200_OK
        state = CardState.objects.get()

        assert (state.level, state.step) == (0, 1)

    @signature
    def test_press_from_the_future_is_trimmed(self, client, form, django_assert_num_queries):
        """Часы клиента, убежавшие вперёд, не увозят карточку из расписания на годы."""
        ahead = datetime(2030, 1, 1, tzinfo=UTC)

        with django_assert_num_queries(9):
            send(client, [answer(f"w{form.pk}", "know", at=ahead)])

        assert CardState.objects.get().answered_at < ahead

    @signature
    def test_future_batch_still_closes_the_card(self, client, form, django_assert_num_queries):
        """Пачка с убежавших вперёд часов закрывает карточку так же, как всякая другая.

        Обрезка каждого нажатия по отдельности слепила бы их в одно время, и вторая
        сторона сошла бы за повтор первой: карточка застряла бы в изучении навсегда.
        """
        card_id = f"w{form.pk}"
        ahead = datetime(2030, 1, 1, tzinfo=UTC)

        with django_assert_num_queries(11):
            sent = send(
                client,
                [
                    answer(card_id, "know", at=ahead),
                    answer(card_id, "know", at=ahead + timedelta(seconds=20)),
                ],
            )

        assert [(state["level"], state["step"]) for state in sent.json()] == [(0, 1), (3, 0)]
        assert CardState.objects.get().level == 3

    @signature
    def test_unknown_card_is_skipped(self, client, form, django_assert_num_queries):
        """Номер удалённой карточки не валит пачку целиком."""
        with django_assert_num_queries(9):
            sent = send(client, [answer("w999999", "know"), answer(f"w{form.pk}", "forgot")])

        assert [state["id"] for state in sent.json()] == [f"w{form.pk}"]
        assert CardState.objects.get().level == 0

    @signature
    def test_phrase_is_answered_too(self, client, phrase, django_assert_num_queries):
        """Фразы оцениваются так же, как формы слов."""
        with django_assert_num_queries(9):
            sent = send(client, [answer(f"p{phrase.pk}", "know")])

        assert sent.json()[0]["id"] == f"p{phrase.pk}"

    @signature
    def test_answers_belong_to_the_signed_learner(self, client, form, django_assert_num_queries):
        """Оценка ложится тому, кто подписался, а не всем сразу."""
        stranger = Learner.objects.create(telegram_id=8008)

        with django_assert_num_queries(9):
            send(client, [answer(f"w{form.pk}", "know")])

        assert CardState.objects.exclude(learner=stranger).count() == 1
        assert CardState.objects.filter(learner=stranger).count() == 0


@pytest.mark.django_db
class TestAnswersRefused:
    """Кого и что ручка не принимает: без подписи, битую пачку, слишком много."""

    def test_stranger_cannot_answer(self, client, form, django_assert_num_queries):
        """Без подписи оценка не принимается: писать её некуда."""
        with django_assert_num_queries(0):
            sent = send(client, [answer(f"w{form.pk}", "know")], signed=False)

        assert sent.status_code == status.HTTP_403_FORBIDDEN
        assert CardState.objects.count() == 0

    @signature
    @pytest.mark.parametrize(
        "answers",
        [
            [],
            [{"card_id": "12", "verdict": "know", "answered_at": PRESSED.isoformat()}],
            [{"card_id": "w12", "verdict": "может быть", "answered_at": PRESSED.isoformat()}],
            [{"card_id": "x12", "verdict": "know", "answered_at": PRESSED.isoformat()}],
            [{"card_id": "w12", "verdict": "know"}],
        ],
        ids=["пусто", "номер без буквы", "чужая оценка", "чужая буква", "без времени нажатия"],
    )
    def test_broken_batch_is_refused(self, client, answers):
        """Пустая пачка, чужой номер, неизвестная оценка и оценка без времени не проходят."""
        assert send(client, answers).status_code == status.HTTP_400_BAD_REQUEST

    @signature
    def test_batch_longer_than_the_limit_is_refused(self, client, form):
        """Пачку сверх предела ручка не принимает."""
        answers = [answer(f"w{form.pk}", "know")] * 101

        assert send(client, answers).status_code == status.HTTP_400_BAD_REQUEST
        assert CardState.objects.count() == 0

    @signature
    def test_too_many_requests_are_refused(self, client, form, monkeypatch):
        """Оценки нельзя присылать сколько угодно: сверх предела ручка отвечает 429."""
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"answers": "1/hour"})
        answers = [answer(f"w{form.pk}", "know")]

        assert send(client, answers).status_code == status.HTTP_200_OK
        assert send(client, answers).status_code == status.HTTP_429_TOO_MANY_REQUESTS
