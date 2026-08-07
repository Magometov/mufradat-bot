import pytest
from rest_framework.test import APIClient

from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme

pytestmark = pytest.mark.django_db

THEMES = "/api/v1/themes/"
ENTRIES = "/api/v1/entries/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_themes_come_in_button_order(client: APIClient) -> None:
    """Приложение рисует кнопки в том порядке, в каком получило темы."""
    body = client.get(THEMES).json()

    assert [theme["slug"] for theme in body] == list(Theme.values)


def test_theme_carries_its_russian_name(client: APIClient) -> None:
    """Название приходит с сервера, чтобы не расходиться с админкой."""
    body = client.get(THEMES).json()

    assert body[0] == {"slug": "numbers", "name": "Цифры"}


def test_card_carries_its_themes(client: APIClient) -> None:
    """Фильтр по теме считает приложение, поэтому темы едут вместе с колодой."""
    Entry.objects.create(
        arabic="وَالِدِي طَبِيبٌ",
        translation_ru="мой отец врач",
        themes=[Theme.FAMILY, Theme.NOUNS],
    )

    body = client.get(ENTRIES).json()

    assert body[0]["themes"] == ["family", "nouns"]


def test_deck_still_arrives_unfiltered(client: APIClient) -> None:
    """Сервер не фильтрует: одна колода на все кнопки, переключение без запроса."""
    Entry.objects.create(arabic="بَيْت", translation_ru="дом", themes=[Theme.NOUNS])
    Entry.objects.create(arabic="أَنَا", translation_ru="я", themes=[Theme.QUESTIONS])

    assert len(client.get(f"{ENTRIES}?theme=nouns").json()) == 2
