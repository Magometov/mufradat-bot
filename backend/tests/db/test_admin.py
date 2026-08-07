import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_client(client, django_user_model):
    django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="pw"
    )
    client.force_login(django_user_model.objects.get(username="admin"))
    return client


def test_changelist_opens(staff_client) -> None:
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")

    response = staff_client.get("/admin/vocabulary/entry/")

    assert response.status_code == 200
    assert "дом" in response.content.decode()


def test_add_form_opens(staff_client) -> None:
    assert staff_client.get("/admin/vocabulary/entry/add/").status_code == 200


def test_word_is_added_through_admin(staff_client) -> None:
    """Ввод с компьютера идёт через админку — форма должна сохранять слово."""
    response = staff_client.post(
        "/admin/vocabulary/entry/add/",
        {
            "arabic": "كِتَاب",
            "translation_ru": "книга",
            "transliteration": "kitab",
        },
    )

    assert response.status_code == 302
    assert Entry.objects.get(translation_ru="книга").arabic == "كِتَاب"


def test_search_by_russian(staff_client) -> None:
    Entry.objects.create(arabic="كِتَاب", translation_ru="книга")
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")

    body = staff_client.get("/admin/vocabulary/entry/?q=книга").content.decode()

    assert "книга" in body
    assert "دом" not in body


@pytest.fixture
def two_entries_one_with_image() -> None:
    Entry.objects.create(
        arabic="كِتَاب",
        translation_ru="книга",
        image=SimpleUploadedFile("kitab.jpg", b"jpeg"),
    )
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")


def test_filter_shows_only_entries_with_image(staff_client, two_entries_one_with_image) -> None:
    body = staff_client.get("/admin/vocabulary/entry/?has_image=yes").content.decode()

    assert "книга" in body
    assert "дом" not in body


def test_filter_shows_only_entries_without_image(staff_client, two_entries_one_with_image) -> None:
    body = staff_client.get("/admin/vocabulary/entry/?has_image=no").content.decode()

    assert "дом" in body
    assert "книга" not in body


@pytest.fixture
def entries_across_themes() -> None:
    Entry.objects.create(
        arabic="وَالِدِي طَبِيبٌ",
        translation_ru="мой отец врач",
        themes=[Theme.FAMILY, Theme.NOUNS],
    )
    Entry.objects.create(arabic="بَيْت", translation_ru="дом", themes=[Theme.NOUNS])
    Entry.objects.create(arabic="عَيْن", translation_ru="глаз")


def test_filter_shows_cards_of_one_theme(staff_client, entries_across_themes) -> None:
    body = staff_client.get("/admin/vocabulary/entry/?theme=family").content.decode()

    assert "мой отец врач" in body
    assert "дом" not in body


def test_filter_finds_cards_left_without_theme(staff_client, entries_across_themes) -> None:
    """Скрипт простановки оставляет остаток — его надо уметь найти глазами."""
    body = staff_client.get("/admin/vocabulary/entry/?theme=none").content.decode()

    assert "глаз" in body
    assert "дом" not in body


def test_themes_are_edited_by_checkboxes(staff_client) -> None:
    body = staff_client.get("/admin/vocabulary/entry/add/").content.decode()

    assert 'type="checkbox" name="themes" value="family"' in body


def test_themes_are_saved_from_admin_form(staff_client) -> None:
    response = staff_client.post(
        "/admin/vocabulary/entry/add/",
        {
            "arabic": "كِتَاب",
            "translation_ru": "книга",
            "transliteration": "kitab",
            "themes": ["nouns", "questions"],
        },
    )

    assert response.status_code == 302
    assert Entry.objects.get(translation_ru="книга").themes == ["nouns", "questions"]


def test_word_without_themes_still_saves(staff_client) -> None:
    """Бот добавляет слова без темы, и админка не должна требовать больше бота."""
    response = staff_client.post(
        "/admin/vocabulary/entry/add/",
        {"arabic": "عَيْن", "translation_ru": "глаз", "transliteration": "ayn"},
    )

    assert response.status_code == 302
    assert Entry.objects.get(translation_ru="глаз").themes == []
