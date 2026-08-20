"""Ручка состояния: кому видна новая логика и что уезжает в приложение."""

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.constants import INIT_DATA_HEADER
from apps.common.models import Learner
from apps.learning.services import apply
from tests.test_telegram import TOKEN, init_data

URL = "/api/v1/state/"

signature = override_settings(BOT_TOKEN=TOKEN)


def ask(client: APIClient, *, signed: bool = False):
    """Спрашивает состояние. С подписью — от опознанного человека."""
    headers = {INIT_DATA_HEADER: init_data()} if signed else {}

    return client.get(URL, headers=headers)


@pytest.mark.django_db
class TestStateAccess:
    """Кому видна новая логика: подпись опознаёт, галочка включает."""

    def test_stranger_gets_rules_but_no_cards(self, client, django_assert_num_queries):
        """Неопознанному новая логика не видна, но правила приезжают: они не секрет."""
        with django_assert_num_queries(0):
            response = ask(client)

        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert body["enabled"] is False
        assert body["cards"] == []
        assert body["ladder"]

    @signature
    def test_signature_without_the_checkbox_is_not_enough(self, client, django_assert_num_queries):
        """Подпись опознаёт человека, но логику включает галочка."""
        with django_assert_num_queries(5):
            body = ask(client, signed=True).json()

        assert body["enabled"] is False
        assert Learner.objects.get().scheduling is False

    @signature
    def test_checkbox_turns_the_logic_on(self, client, django_assert_num_queries):
        """Галочка в админке — единственный способ включить логику до открытия всем."""
        ask(client, signed=True)
        Learner.objects.update(scheduling=True)

        with django_assert_num_queries(2):
            response = ask(client, signed=True)

        assert response.json()["enabled"] is True

    @override_settings(SCHEDULING_FOR_ALL=True, BOT_TOKEN=TOKEN)
    def test_open_to_all_ignores_the_checkbox(self, client, django_assert_num_queries):
        """Открыли всем — галочка больше не нужна, но опознание нужно."""
        with django_assert_num_queries(5):
            response = ask(client, signed=True)

        assert response.json()["enabled"] is True

    @override_settings(SCHEDULING_FOR_ALL=True)
    def test_stranger_gets_nothing_even_when_open_to_all(self, client, django_assert_num_queries):
        """Неопознанному логика не включается: его оценки некуда писать."""
        with django_assert_num_queries(0):
            response = ask(client)

        assert response.json()["enabled"] is False


@pytest.mark.django_db
class TestStateContents:
    """Что уезжает в приложение: правила из настроек и свой прогресс."""

    @override_settings(
        LADDER=[2, 9],
        JITTER_PERCENT=4,
        FIRST_SIGHT_LEVEL=2,
        SIDES_NEEDED=3,
        LAPSE_DROP=3,
        ANSWERS_LIMIT=5,
    )
    def test_rules_travel_as_data(self, client, django_assert_num_queries):
        """Правила уезжают в приложение из настроек: считать сеанс будет оно."""
        with django_assert_num_queries(0):
            body = ask(client).json()

        assert body["ladder"] == [2, 9]
        assert body["jitter"] == 4
        assert body["first_sight_level"] == 2
        assert body["needed"] == 3
        assert body["lapse_drop"] == 3
        assert body["answers_limit"] == 5
        assert body["now"]

    # Ступеней взято ровно столько, сколько закрывает карточку: иначе тест зависел бы
    # от строгости, заданной в окружении.
    @override_settings(BOT_TOKEN=TOKEN, SIDES_NEEDED=2)
    def test_cards_carry_level_fall_and_due(self, client, form, phrase, django_assert_num_queries):
        """Карточки приезжают с уровнем, промахами, падением и сроком — под номерами приложения."""
        ask(client, signed=True)
        learner = Learner.objects.get()
        apply(learner=learner, card=form, knows=True)
        apply(learner=learner, card=form, knows=True)
        apply(learner=learner, card=phrase, knows=False)

        with django_assert_num_queries(2):
            response = ask(client, signed=True)

        cards = {card["id"]: card for card in response.json()["cards"]}

        assert cards[f"w{form.pk}"]["level"] > 0
        assert cards[f"w{form.pk}"]["lapses"] == 0
        assert cards[f"p{phrase.pk}"]["level"] == 0
        assert cards[f"p{phrase.pk}"]["lapses"] == 1
        assert cards[f"p{phrase.pk}"]["lapsed_from"] == 0
        assert cards[f"p{phrase.pk}"]["due_at"]

    @signature
    def test_foreign_progress_stays_foreign(self, client, form, django_assert_num_queries):
        """Чужие карточки в ответ не попадают."""
        stranger = Learner.objects.create(telegram_id=5005)
        apply(learner=stranger, card=form, knows=True)

        with django_assert_num_queries(5):
            response = ask(client, signed=True)

        assert response.json()["cards"] == []
