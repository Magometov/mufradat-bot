"""Ручка оценок: пачка, пределы и кто её вправе присылать."""

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.common.constants import INIT_DATA_HEADER
from apps.common.models import Learner
from apps.learning.models import CardState
from tests.test_telegram import TOKEN, init_data

URL = "/api/v1/answers/"

signature = override_settings(
    BOT_TOKEN=TOKEN, LADDER=[1, 2, 3, 4, 5], JITTER_PERCENT=0, FIRST_SIGHT_LEVEL=3
)


@pytest.fixture
def client() -> APIClient:
    cache.clear()

    return APIClient()


def send(client: APIClient, answers: list[dict], *, signed: bool = True):
    headers = {INIT_DATA_HEADER: init_data()} if signed else {}

    return client.post(URL, {"answers": answers}, format="json", headers=headers)


@pytest.mark.django_db
def test_stranger_cannot_answer(client, form):
    """Без подписи оценка не принимается: писать её некуда."""
    answer = send(client, [{"card_id": f"w{form.pk}", "verdict": "know"}], signed=False)

    assert answer.status_code == 403
    assert CardState.objects.count() == 0


@signature
@pytest.mark.django_db
def test_answer_is_applied_and_returned(client, form):
    """Оценка записывается, а в ответ едет новое состояние карточки."""
    answer = send(client, [{"card_id": f"w{form.pk}", "verdict": "know"}])

    assert answer.status_code == 200

    state = CardState.objects.get()
    card = answer.json()[0]
    assert (card["id"], card["level"], card["step"]) == (f"w{form.pk}", 3, 0)
    assert parse_datetime(card["due_at"]) == state.due_at


@signature
@pytest.mark.django_db
def test_batch_is_applied_in_order(client, form):
    """Пачка применяется по порядку: два «помню» поднимают на два уровня."""
    card_id = f"w{form.pk}"

    answer = send(
        client,
        [{"card_id": card_id, "verdict": "know"}, {"card_id": card_id, "verdict": "know"}],
    )

    assert [state["level"] for state in answer.json()] == [3, 4]
    assert CardState.objects.get().level == 4


@signature
@pytest.mark.django_db
def test_unknown_card_is_skipped(client, form):
    """Номер удалённой карточки не валит пачку целиком."""
    answer = send(
        client,
        [
            {"card_id": "w999999", "verdict": "know"},
            {"card_id": f"w{form.pk}", "verdict": "forgot"},
        ],
    )

    assert [state["id"] for state in answer.json()] == [f"w{form.pk}"]
    assert CardState.objects.get().level == 0


@signature
@pytest.mark.django_db
def test_phrase_is_answered_too(client, phrase):
    """Фразы оцениваются так же, как формы слов."""
    answer = send(client, [{"card_id": f"p{phrase.pk}", "verdict": "know"}])

    assert answer.json()[0]["id"] == f"p{phrase.pk}"


@signature
@pytest.mark.django_db
@pytest.mark.parametrize(
    "answers",
    [
        [],
        [{"card_id": "12", "verdict": "know"}],
        [{"card_id": "w12", "verdict": "может быть"}],
        [{"card_id": "x12", "verdict": "know"}],
    ],
)
def test_broken_batch_is_refused(client, answers):
    """Пустая пачка, чужой формат номера и неизвестная оценка не проходят проверку."""
    assert send(client, answers).status_code == 400


@signature
@pytest.mark.django_db
def test_batch_longer_than_the_limit_is_refused(client, form):
    """Пачку сверх предела ручка не принимает."""
    answers = [{"card_id": f"w{form.pk}", "verdict": "know"}] * 101

    assert send(client, answers).status_code == 400
    assert CardState.objects.count() == 0


@signature
@pytest.mark.django_db
def test_too_many_requests_are_refused(client, form, monkeypatch):
    """Оценки нельзя присылать сколько угодно: сверх предела ручка отвечает 429."""
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"answers": "1/hour"})
    answers = [{"card_id": f"w{form.pk}", "verdict": "know"}]

    assert send(client, answers).status_code == 200
    assert send(client, answers).status_code == 429


@signature
@pytest.mark.django_db
def test_answers_belong_to_the_signed_learner(client, form):
    """Оценка ложится тому, кто подписался, а не всем сразу."""
    stranger = Learner.objects.create(telegram_id=8008)

    send(client, [{"card_id": f"w{form.pk}", "verdict": "know"}])

    assert CardState.objects.exclude(learner=stranger).count() == 1
    assert CardState.objects.filter(learner=stranger).count() == 0
