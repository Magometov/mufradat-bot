"""Адрес картинки: бэкенд отдаёт путь, публичный хост подставляет бот."""

import pytest

from bot import api, config


@pytest.fixture(autouse=True)
def webapp(monkeypatch):
    """Публичный адрес приложения задаёт тест, а не окружение машины."""
    monkeypatch.setattr(config, "WEBAPP_URL", "https://mufradat.example/")


class TestImageUrl:
    """Адрес картинки для Telegram: путь от бэкенда плюс публичный хост."""

    def test_path_becomes_a_public_address(self):
        """Путь от бэкенда превращается в ссылку, которую Telegram сможет скачать."""
        assert api._image_url("/m/cards/w12.webp") == "https://mufradat.example/m/cards/w12.webp"

    def test_card_without_a_picture_stays_without_one(self):
        """Пустой путь остаётся пустым: карточка уедет текстом."""
        assert api._image_url(None) is None

    def test_without_the_public_address_the_picture_is_dropped(self, monkeypatch):
        """Собрать адрес не из чего — картинки нет, но слово всё равно уедет."""
        monkeypatch.setattr(config, "WEBAPP_URL", None)

        assert api._image_url("/m/cards/w12.webp") is None
