"""Адрес картинки: бэкенд отдаёт путь, публичный хост подставляет бот."""

import pytest

from bot import api, config
from bot.api import Lesson, Unit


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


class TestLessonOfKind:
    """Разбор раздела идёт по одному виду: партия слов — слова, партия фраз — фразы."""

    LESSON = Lesson(
        units=[Unit("word", 1, "книга"), Unit("phrase", 2, "привет"), Unit("word", 3, "дом")],
        themes=[("family", "Семья")],
    )

    def test_only_units_of_the_asked_kind_are_left(self):
        """Добавляли фразы — слова в разбор не попадают, и наоборот."""
        assert [unit.title for unit in self.LESSON.of_kind("phrase").units] == ["привет"]
        assert [unit.title for unit in self.LESSON.of_kind("word").units] == ["книга", "дом"]

    def test_themes_stay_whole(self):
        """Темы не режутся: раскладывают по тем же, что и раньше."""
        assert self.LESSON.of_kind("phrase").themes == self.LESSON.themes

    def test_kind_without_units_leaves_nothing_to_sort(self):
        """Своего вида в разделе нет — разбирать нечего, и предложения не будет."""
        assert Lesson(units=[Unit("word", 1, "книга")], themes=[]).of_kind("phrase").units == []
