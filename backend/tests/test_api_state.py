"""Ручка состояния: кому видна новая логика и что уезжает в приложение."""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.common.constants import INIT_DATA_HEADER
from apps.common.models import Learner
from apps.learning.services import apply
from tests.test_telegram import TOKEN, init_data

URL = "/api/v1/state/"

signature = override_settings(BOT_TOKEN=TOKEN)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def ask(client: APIClient, *, signed: bool = False):
    headers = {INIT_DATA_HEADER: init_data()} if signed else {}

    return client.get(URL, headers=headers)


@pytest.mark.django_db
def test_stranger_gets_rules_but_no_cards(client):
    """Неопознанному новая логика не видна, но правила приезжают: они не секрет."""
    body = ask(client).json()

    assert body["enabled"] is False
    assert body["cards"] == []
    assert body["ladder"]


@signature
@pytest.mark.django_db
def test_signature_without_the_checkbox_is_not_enough(client):
    """Подпись опознаёт человека, но логику включает галочка."""
    body = ask(client, signed=True).json()

    assert body["enabled"] is False
    assert Learner.objects.get().scheduling is False


@signature
@pytest.mark.django_db
def test_checkbox_turns_the_logic_on(client):
    """Галочка в админке — единственный способ включить логику до открытия всем."""
    ask(client, signed=True)
    Learner.objects.update(scheduling=True)

    assert ask(client, signed=True).json()["enabled"] is True


@override_settings(SCHEDULING_FOR_ALL=True)
@pytest.mark.django_db
def test_open_to_all_ignores_the_checkbox(client):
    """Открыли всем — видно и без подписи, и без галочки."""
    assert ask(client).json()["enabled"] is True


@override_settings(
    LADDER=[2, 9], JITTER_PERCENT=4, SESSION_LIMIT=7, NEW_LIMIT=3, FIRST_SIGHT_LEVEL=2
)
@pytest.mark.django_db
def test_rules_travel_as_data(client):
    """Правила уезжают в приложение из настроек: считать сеанс будет оно."""
    body = ask(client).json()

    assert body["ladder"] == [2, 9]
    assert body["jitter"] == 4
    assert body["session_limit"] == 7
    assert body["new_limit"] == 3
    assert body["first_sight_level"] == 2
    assert body["needed"] == 2
    assert body["now"]


@signature
@pytest.mark.django_db
def test_cards_carry_level_and_due(client, form, phrase):
    """Карточки приезжают с уровнем, счётом и сроком — под номерами приложения."""
    ask(client, signed=True)
    learner = Learner.objects.get()
    apply(learner=learner, card=form, knows=True)
    apply(learner=learner, card=phrase, knows=False)

    cards = {card["id"]: card for card in ask(client, signed=True).json()["cards"]}

    assert cards[f"w{form.pk}"]["level"] > 0
    assert cards[f"p{phrase.pk}"]["level"] == 0
    assert cards[f"p{phrase.pk}"]["due_at"]


@signature
@pytest.mark.django_db
def test_foreign_progress_stays_foreign(client, form):
    """Чужие карточки в ответ не попадают."""
    stranger = Learner.objects.create(telegram_id=5005)
    apply(learner=stranger, card=form, knows=True)

    assert ask(client, signed=True).json()["cards"] == []
