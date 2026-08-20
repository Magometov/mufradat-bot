"""Служебная ручка поиска: кто её вправе звать и что она отдаёт."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.api.internal.views import search as view
from apps.vocabulary.constants import SEARCH_LIMIT
from apps.vocabulary.services import postcard_url

URL = "/api/v1/internal/search/"

TOKEN = "bot-secret"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def ask(client: APIClient, **params):
    """Спрашивает поиск от имени бота."""
    return client.get(URL, params, headers={HEADER: TOKEN})


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


@pytest.mark.django_db
class TestSearch:
    """Поиск для инлайна: доступ, номера карточек, картинка и потолок выдачи."""

    @pytest.fixture(autouse=True)
    def bot_token(self, settings) -> None:
        """Секрет бота задаёт тест: с пустым ручка не пустила бы никого."""
        settings.BOT_API_TOKEN = TOKEN

    def test_stranger_gets_nothing(self, client, form, django_assert_num_queries):
        """Без общего секрета ручка не отвечает: наружу она не выпускается вовсе."""
        with django_assert_num_queries(0):
            response = client.get(URL, {"query": "книга"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_card_comes_with_its_number(self, client, form, django_assert_num_queries):
        """Номер тот же, что у приложения: им инлайн различает свои результаты."""
        with django_assert_num_queries(2):
            found = ask(client, query="книга").json()

        assert found == [
            {
                "id": f"w{form.pk}",
                "arabic": form.arabic,
                "translation_ru": "книга",
                "transliteration": "",
                "image": postcard_url(form),
            }
        ]

    def test_inline_gets_the_postcard(self, client, form, django_assert_num_queries):
        """В инлайн уезжает адрес собранной карточки, а не иллюстрации."""
        form.image.save("probe.png", picture(), save=True)

        with django_assert_num_queries(2):
            found = ask(client, query="книга").json()

        assert found[0]["image"] == postcard_url(form)

    def test_nothing_found_is_an_empty_list(self, client, form, django_assert_num_queries):
        """Ничего не нашлось — пустой список, а не отказ."""
        with django_assert_num_queries(2):
            answer = ask(client, query="самолёт")

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == []

    def test_the_ceiling_is_the_backends_own(self, client, form, monkeypatch):
        """Потолок ставит бэкенд, а не проситель: столько инлайн всё равно не покажет."""
        asked = []
        monkeypatch.setattr(view, "find", lambda query, **kwargs: asked.append(kwargs) or [])

        ask(client, query="книга", limit=1000)

        assert asked == [{"limit": SEARCH_LIMIT}]

    def test_query_may_be_missing(self, client, form, django_assert_num_queries):
        """Без строки поиска ручка отдаёт свежее, а не отказывает."""
        with django_assert_num_queries(2):
            answer = ask(client)

        assert answer.status_code == status.HTTP_200_OK
