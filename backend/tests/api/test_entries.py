from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.vocabulary.models import Entry

pytestmark = pytest.mark.django_db

ENTRIES = "/api/v1/entries/"


@pytest.fixture(autouse=True)
def media(settings, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_deck_is_one_flat_list(client: APIClient) -> None:
    """Деления на слова и фразы нет: приложение получает всё одним списком и тасует."""
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")
    Entry.objects.create(arabic="مَا اسْمُكَ؟", translation_ru="как тебя зовут?")

    body = client.get(ENTRIES).json()

    assert len(body) == 2
    assert "kind" not in body[0]


def test_entry_has_everything_for_both_sides(client: APIClient) -> None:
    entry = Entry.objects.create(arabic="بَيْت", translation_ru="дом", transliteration="bayt")

    body = client.get(ENTRIES).json()

    assert body == [
        {
            "id": entry.pk,
            "arabic": "بَيْت",
            "translation_ru": "дом",
            "transliteration": "bayt",
            "image": None,
        }
    ]


def test_image_comes_as_full_url(client: APIClient) -> None:
    """Mini App живёт на другом домене, поэтому относительный путь ему бесполезен."""
    Entry.objects.create(
        arabic="بَيْت",
        translation_ru="дом",
        image=SimpleUploadedFile("bayt.jpg", b"jpeg"),
    )

    image = client.get(ENTRIES).json()[0]["image"]

    assert image.startswith("http://testserver/m/entries/bayt")


def test_newest_entries_come_first(client: APIClient) -> None:
    """Порядок задан, чтобы ответ не плавал от запроса к запросу; тасует приложение."""
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")
    Entry.objects.create(arabic="كِتَاب", translation_ru="книга")

    body = client.get(ENTRIES).json()

    assert [item["translation_ru"] for item in body] == ["книга", "дом"]


def test_whole_deck_arrives_in_one_response(client: APIClient) -> None:
    """Прогон — снимок, взятый одним запросом: постраничность его бы разрезала."""
    Entry.objects.bulk_create(
        Entry(arabic=f"كلمة{number}", translation_ru=f"слово {number}") for number in range(120)
    )

    body = client.get(ENTRIES).json()

    assert len(body) == 120
