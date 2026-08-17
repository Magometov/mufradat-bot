"""Служебная ручка поиска: кто её вправе звать и что она отдаёт."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.api.internal.views import search as view
from apps.vocabulary.constants import SEARCH_LIMIT

URL = "/api/v1/internal/search/"

TOKEN = "bot-secret"

signed = override_settings(BOT_API_TOKEN=TOKEN)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def ask(client: APIClient, **params) -> object:
    return client.get(URL, params, headers={HEADER: TOKEN})


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


@signed
@pytest.mark.django_db
def test_stranger_gets_nothing(client, form):
    """Без общего секрета ручка не отвечает: наружу она не выпускается вовсе."""
    assert client.get(URL, {"query": "книга"}).status_code == 403


@signed
@pytest.mark.django_db
def test_card_comes_with_its_number(client, form):
    """Номер тот же, что у приложения: им инлайн различает свои результаты."""
    found = ask(client, query="книга").json()

    assert found == [
        {
            "id": f"w{form.pk}",
            "arabic": form.arabic,
            "translation_ru": "книга",
            "transliteration": "",
            "image": None,
        }
    ]


@signed
@pytest.mark.django_db
def test_inline_gets_the_postcard(client, form):
    """В инлайн уезжает собранная карточка, и путём, а не адресом: хост знает бот."""
    form.image.save("probe.png", picture(), save=True)

    assert ask(client, query="книга").json()[0]["image"] == f"/api/v1/card/w{form.pk}.jpg"


@signed
@pytest.mark.django_db
def test_nothing_found_is_an_empty_list(client, form):
    """Ничего не нашлось — пустой список, а не отказ."""
    answer = ask(client, query="самолёт")

    assert answer.status_code == 200
    assert answer.json() == []


@signed
@pytest.mark.django_db
def test_the_ceiling_is_the_backends_own(client, form, monkeypatch):
    """Потолок ставит бэкенд, а не проситель: столько инлайн всё равно не покажет."""
    asked = []
    monkeypatch.setattr(view, "find", lambda query, **kwargs: asked.append(kwargs) or [])

    ask(client, query="книга", limit=1000)

    assert asked == [{"limit": SEARCH_LIMIT}]


@signed
@pytest.mark.django_db
def test_query_may_be_missing(client, form):
    """Без строки поиска ручка отдаёт свежее, а не отказывает."""
    assert ask(client).status_code == 200
