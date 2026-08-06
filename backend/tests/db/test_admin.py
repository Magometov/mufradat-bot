import pytest

from apps.vocabulary.models import Entry

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
