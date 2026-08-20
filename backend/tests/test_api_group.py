"""Служебная ручка слова для группы: кто её вправе звать и что она отдаёт."""

from datetime import datetime
from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.timezone import make_aware
from PIL import Image
from rest_framework import status

from apps.api.internal.permissions import HEADER
from apps.learning.models import GroupPost
from apps.vocabulary.services import postcard_url

URL = "/api/v1/internal/group/take/"

TOKEN = "bot-secret"
CHAT = -1001

# Слоты рассылки в группу — 10 и 18 часов по Москве; часы в настройках проекта московские.
MORNING = make_aware(datetime(2026, 8, 17, 10, 4))
NIGHT = make_aware(datetime(2026, 8, 17, 3, 0))


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


@pytest.mark.django_db
class TestGroupCard:
    """Слово для группы: кому ручка отвечает, что отдаёт и когда молчит."""

    @pytest.fixture(autouse=True)
    def group_settings(self, settings) -> None:
        """Секрет бота и id группы задаёт тест: от окружения ответ зависеть не должен."""
        settings.BOT_API_TOKEN = TOKEN
        settings.GROUP_CHAT_ID = CHAT

    @pytest.fixture
    def morning(self, monkeypatch) -> None:
        """Часы стоят на утреннем слоте: иначе ответ зависел бы от времени прогона."""
        monkeypatch.setattr(timezone, "now", lambda: MORNING)

    def test_stranger_gets_nothing(self, client, django_assert_num_queries):
        """Без общего секрета ручка не отвечает: наружу она не выпускается вовсе."""
        with django_assert_num_queries(0):
            response = client.post(URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_card_carries_the_group_id(self, client, form, morning, django_assert_num_queries):
        """Куда слать, знает бэкенд: id группы едет в ответе, бот его не хранит."""
        with django_assert_num_queries(3):
            answer = client.post(URL, headers={HEADER: TOKEN})

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {
            "chat_id": CHAT,
            "arabic": form.arabic,
            "translation_ru": form.translation_ru,
            "transliteration": "",
            "image": postcard_url(form),
        }
        assert GroupPost.objects.get().card == form

    def test_nothing_to_send_is_no_content(self, client, form, monkeypatch):
        """Слот не наступил — пустой ответ, а не пустая карточка."""
        monkeypatch.setattr(timezone, "now", lambda: NIGHT)

        answer = client.post(URL, headers={HEADER: TOKEN})

        assert answer.status_code == status.HTTP_204_NO_CONTENT
        assert answer.content == b""
        assert GroupPost.objects.count() == 0

    def test_group_gets_the_postcard(self, client, form, morning):
        """В группу уезжает собранная карточка, и путём, а не адресом: хост знает бот."""
        form.image.save("probe.png", picture(), save=True)

        image = client.post(URL, headers={HEADER: TOKEN}).json()["image"]

        assert image == postcard_url(form)

    def test_forced_ignores_the_slot(self, client, form, monkeypatch):
        """Просьба прислать сейчас доезжает до выборки: ночью слово уедет только с ней."""
        monkeypatch.setattr(timezone, "now", lambda: NIGHT)

        refused = client.post(URL, headers={HEADER: TOKEN})
        forced = client.post(URL, {"forced": True}, format="json", headers={HEADER: TOKEN})

        assert refused.status_code == status.HTTP_204_NO_CONTENT
        assert forced.status_code == status.HTTP_200_OK
