"""Картинки для чата: когда готовятся и какой адрес получают."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings
from PIL import Image

from apps.vocabulary.models import Phrase
from apps.vocabulary.services import postcard_url

# Бакет как на сервере, только адрес выдуманный: `url()` строит строку, никуда не ходя.
BUCKET = override_settings(
    STORAGES={
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": "mufradat-media",
                "custom_domain": "pub-test.r2.dev",
                "access_key": "k",
                "secret_key": "s",
                "querystring_auth": False,
                "region_name": "auto",
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)


def picture() -> ContentFile:
    """Картинка, которую примет `ImageField`."""
    buffer = BytesIO()
    Image.new("RGB", (400, 400), "red").save(buffer, format="PNG")

    return ContentFile(buffer.getvalue(), name="probe.png")


def ready() -> list[str]:
    """Что лежит в каталоге готового для чата."""
    return sorted(default_storage.listdir("telegram")[1])


@pytest.fixture
def drawn(form):
    """Карточка с картинкой: сохранение уже собрало для неё всё нужное."""
    form.image.save("probe.png", picture(), save=True)

    return form


@pytest.mark.django_db
def test_saving_a_card_prepares_its_picture(drawn):
    """Собирается при сохранении, а не по запросу: инлайн показывает полсотни разом."""
    assert len(ready()) == 1


@pytest.mark.django_db
def test_the_address_points_at_the_prepared_file(drawn):
    """Адрес ведёт ровно к тому файлу, который лежит рядом."""
    assert postcard_url(drawn).endswith(ready()[0])


@pytest.mark.django_db
def test_the_postcard_is_a_jpeg(drawn):
    """Инлайн Telegram принимает только джипег."""
    name = next(name for name in ready() if name.startswith("card-"))

    with default_storage.open(f"telegram/{name}") as file:
        assert file.read(2) == b"\xff\xd8"


@pytest.mark.django_db
def test_editing_the_text_prepares_new_files(drawn):
    """Правка текста даёт новые файлы: иначе в чат уезжала бы прошлая карточка."""
    before = postcard_url(drawn)
    drawn.translation_ru = "очки"
    drawn.save(update_fields=["translation_ru"])

    assert postcard_url(drawn) != before
    assert len(ready()) == 2


@pytest.mark.django_db
def test_saving_twice_prepares_nothing_new(drawn):
    """Второе сохранение ничего не пересобирает: имя файла то же."""
    drawn.save()

    assert len(ready()) == 1


@pytest.mark.django_db
def test_the_bucket_gives_an_absolute_address(drawn):
    """С бакетом адрес абсолютный и ведёт в Cloudflare — до нас Telegram не доходит."""
    with BUCKET:
        assert postcard_url(drawn).startswith("https://pub-test.r2.dev/telegram/card-")


@pytest.mark.django_db
def test_a_card_without_a_picture_has_no_address(form):
    """Собирать нечего — и адреса нет, бот отправит карточку текстом."""
    assert postcard_url(form) is None
    assert not default_storage.exists("telegram")


@pytest.mark.django_db
def test_phrases_are_prepared_too(db):
    """Фразы уезжают в инлайн наравне со словами."""
    phrase = Phrase.objects.create(themes=["greetings"], arabic="بَاب", translation_ru="дверь")
    phrase.image.save("probe.png", picture(), save=True)

    assert postcard_url(phrase) is not None
    assert len(ready()) == 1
