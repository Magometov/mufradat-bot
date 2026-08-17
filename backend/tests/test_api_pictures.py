"""Картинки для Telegram: собранная карточка и голая иллюстрация."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from PIL import Image

POSTCARD = "/api/v1/card/{card_id}.jpg"
PHOTO = "/api/v1/photo/{card_id}.jpg"


@pytest.fixture
def client() -> Client:
    return Client()


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (400, 400), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


@pytest.fixture
def drawn(form) -> object:
    """Карточка с картинкой."""
    form.image.save("probe.png", picture(), save=True)

    return form


def body(answer) -> bytes:
    return b"".join(answer.streaming_content)


@pytest.mark.django_db
def test_postcard_is_a_jpeg(client, drawn):
    """Инлайн Telegram принимает только джипег, поэтому карточка отдаётся им."""
    answer = client.get(POSTCARD.format(card_id=f"w{drawn.pk}"))

    assert answer.status_code == 200
    assert answer["Content-Type"] == "image/jpeg"
    assert body(answer)[:2] == b"\xff\xd8"


@pytest.mark.django_db
def test_postcard_is_drawn_once(client, drawn, settings):
    """Собранное ложится на диск: второй раз карточка не рисуется."""
    address = POSTCARD.format(card_id=f"w{drawn.pk}")
    client.get(address)
    ready = list((settings.MEDIA_ROOT / "telegram").iterdir())

    client.get(address)

    assert len(ready) == 1
    assert list((settings.MEDIA_ROOT / "telegram").iterdir()) == ready


@pytest.mark.django_db
def test_photo_keeps_the_illustration(client, drawn):
    """Голая иллюстрация — та же картинка, только джипегом: её прячет спойлер."""
    answer = client.get(PHOTO.format(card_id=f"w{drawn.pk}"))

    assert answer.status_code == 200
    assert Image.open(BytesIO(body(answer))).size == (400, 400)


@pytest.mark.django_db
def test_card_without_a_picture_is_not_found(client, form):
    """Собирать нечего — честный 404, а не пустая картинка."""
    assert client.get(POSTCARD.format(card_id=f"w{form.pk}")).status_code == 404
    assert client.get(PHOTO.format(card_id=f"w{form.pk}")).status_code == 404


@pytest.mark.django_db
def test_unknown_number_is_not_found(client, form):
    """Чужой номер ничего не отдаёт."""
    assert client.get(POSTCARD.format(card_id="w999999")).status_code == 404
    assert client.get(POSTCARD.format(card_id="мусор")).status_code == 404


@pytest.mark.django_db
def test_edited_card_gets_a_new_file(client, drawn, settings):
    """Правка текста даёт новое имя файлу: иначе в чат уезжала бы прошлая карточка."""
    client.get(POSTCARD.format(card_id=f"w{drawn.pk}"))
    drawn.translation_ru = "очки"
    drawn.save(update_fields=["translation_ru"])

    client.get(POSTCARD.format(card_id=f"w{drawn.pk}"))

    assert len(list((settings.MEDIA_ROOT / "telegram").iterdir())) == 2
