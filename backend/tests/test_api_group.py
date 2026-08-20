"""Служебная ручка слова для группы: кто её вправе звать и что она отдаёт."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.api.internal.views import group as view
from apps.vocabulary.services import postcard_url

URL = "/api/v1/internal/group/take/"

TOKEN = "bot-secret"
CHAT = -1001


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


@pytest.mark.django_db
class TestGroupCard:
    """Слово для группы: кому ручка отвечает, что отдаёт и о чём просит выборку."""

    @pytest.fixture(autouse=True)
    def group_settings(self, settings) -> None:
        """Секрет бота и id группы задаёт тест: от окружения ответ зависеть не должен."""
        settings.BOT_API_TOKEN = TOKEN
        settings.GROUP_CHAT_ID = CHAT

    def test_stranger_gets_nothing(self, client, django_assert_num_queries):
        """Без общего секрета ручка не отвечает: наружу она не выпускается вовсе."""
        with django_assert_num_queries(0):
            response = client.post(URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_card_carries_the_group_id(self, client, monkeypatch, form, django_assert_num_queries):
        """Куда слать, знает бэкенд: id группы едет в ответе, бот его не хранит."""
        monkeypatch.setattr(view, "take_group_card", lambda **kwargs: form)

        with django_assert_num_queries(0):
            answer = client.post(URL, headers={HEADER: TOKEN})

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {
            "chat_id": CHAT,
            "arabic": form.arabic,
            "translation_ru": form.translation_ru,
            "transliteration": "",
            "image": None,
        }

    def test_nothing_to_send_is_no_content(self, client, monkeypatch, django_assert_num_queries):
        """Слот не наступил — пустой ответ, а не пустая карточка."""
        monkeypatch.setattr(view, "take_group_card", lambda **kwargs: None)

        with django_assert_num_queries(0):
            answer = client.post(URL, headers={HEADER: TOKEN})

        assert answer.status_code == status.HTTP_204_NO_CONTENT
        assert answer.content == b""

    def test_group_gets_the_postcard(self, client, monkeypatch, form):
        """В группу уезжает собранная карточка, и путём, а не адресом: хост знает бот."""
        form.image.save("probe.png", picture(), save=True)
        monkeypatch.setattr(view, "take_group_card", lambda **kwargs: form)

        image = client.post(URL, headers={HEADER: TOKEN}).json()["image"]

        assert image == postcard_url(form)

    def test_forced_reaches_the_service(self, client, monkeypatch, form):
        """Просьба прислать сейчас доезжает до выборки, а по умолчанию её нет."""
        asked = []
        monkeypatch.setattr(view, "take_group_card", lambda **kwargs: asked.append(kwargs) or form)

        client.post(URL, headers={HEADER: TOKEN})
        client.post(URL, {"forced": True}, format="json", headers={HEADER: TOKEN})

        assert asked == [{"forced": False}, {"forced": True}]
