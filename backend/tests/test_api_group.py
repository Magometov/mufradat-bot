"""Служебная ручка слова для группы: кто её вправе звать и что она отдаёт."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.api.internal.views import group as view

URL = "/api/v1/internal/group/take/"

TOKEN = "bot-secret"

signed = override_settings(BOT_API_TOKEN=TOKEN, GROUP_CHAT_ID=-1001)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


@signed
@pytest.mark.django_db
def test_stranger_gets_nothing(client):
    """Без общего секрета ручка не отвечает: наружу она не выпускается вовсе."""
    assert client.post(URL).status_code == 403


@signed
@pytest.mark.django_db
def test_card_carries_the_group_id(client, monkeypatch, form):
    """Куда слать, знает бэкенд: id группы едет в ответе, бот его не хранит."""
    monkeypatch.setattr(view, "take_group_card", lambda **kwargs: form)

    answer = client.post(URL, headers={HEADER: TOKEN})

    assert answer.status_code == 200
    assert answer.json() == {
        "chat_id": -1001,
        "arabic": form.arabic,
        "translation_ru": form.translation_ru,
        "transliteration": "",
        "image": None,
    }


@signed
@pytest.mark.django_db
def test_nothing_to_send_is_no_content(client, monkeypatch):
    """Слот не наступил — пустой ответ, а не пустая карточка."""
    monkeypatch.setattr(view, "take_group_card", lambda **kwargs: None)

    answer = client.post(URL, headers={HEADER: TOKEN})

    assert answer.status_code == 204
    assert answer.content == b""


@signed
@pytest.mark.django_db
def test_group_gets_the_postcard(client, monkeypatch, form):
    """В группу уезжает собранная карточка, и путём, а не адресом: хост знает бот."""
    form.image.save("probe.png", picture(), save=True)
    monkeypatch.setattr(view, "take_group_card", lambda **kwargs: form)

    image = client.post(URL, headers={HEADER: TOKEN}).json()["image"]

    assert image == f"/api/v1/card/w{form.pk}.jpg"


@signed
@pytest.mark.django_db
def test_forced_reaches_the_service(client, monkeypatch, form):
    """Просьба прислать сейчас доезжает до выборки, а по умолчанию её нет."""
    asked = []
    monkeypatch.setattr(view, "take_group_card", lambda **kwargs: asked.append(kwargs) or form)

    client.post(URL, headers={HEADER: TOKEN})
    client.post(URL, {"forced": True}, format="json", headers={HEADER: TOKEN})

    assert asked == [{"forced": False}, {"forced": True}]
