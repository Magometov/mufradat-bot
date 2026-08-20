"""Картинки для чата: кто их собирает, когда и какой адрес они получают."""

from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings
from PIL import Image
from rest_framework import status

from apps.vocabulary.constants import Number
from apps.vocabulary.services import add_form, add_phrase, postcard_url, refresh_pictures

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


@pytest.mark.django_db
class TestPostcard:
    """Собранная карточка: файл, адрес и пересборка после правки."""

    @pytest.fixture
    def drawn(self, form):
        """Карточка с картинкой, для которой открытка уже собрана."""
        form.image.save("probe.png", picture(), save=True)
        refresh_pictures(form)

        return form

    def test_prepared_card_lands_in_the_chat_folder(self, drawn):
        """Собирается заранее, а не по запросу: инлайн показывает полсотни результатов разом."""
        assert len(ready()) == 1

    def test_the_address_points_at_the_prepared_file(self, drawn):
        """Адрес ведёт ровно к тому файлу, который лежит рядом."""
        assert postcard_url(drawn).endswith(ready()[0])

    def test_the_postcard_is_a_jpeg(self, drawn):
        """Инлайн Telegram принимает только джипег."""
        name = next(name for name in ready() if name.startswith("card-"))

        with default_storage.open(f"telegram/{name}") as file:
            assert file.read(2) == b"\xff\xd8"

    def test_new_text_gets_a_new_file(self, drawn):
        """Правка текста даёт новые файлы: иначе в чат уезжала бы прошлая карточка."""
        before = postcard_url(drawn)
        drawn.translation_ru = "очки"
        drawn.save(update_fields=["translation_ru"])
        refresh_pictures(drawn)

        assert postcard_url(drawn) != before
        assert len(ready()) == 2

    def test_second_call_prepares_nothing_new(self, drawn):
        """Второй вызов ничего не пересобирает: имя файла то же."""
        refresh_pictures(drawn)

        assert len(ready()) == 1

    def test_the_bucket_gives_an_absolute_address(self, drawn):
        """С бакетом адрес абсолютный и ведёт в Cloudflare — до нас Telegram не доходит."""
        with BUCKET:
            assert postcard_url(drawn).startswith("https://pub-test.r2.dev/telegram/card-")

    def test_a_card_without_a_picture_has_no_address(self, form):
        """Собирать нечего — и адреса нет, бот отправит карточку текстом."""
        refresh_pictures(form)

        assert postcard_url(form) is None
        assert not default_storage.exists("telegram")


@pytest.mark.django_db
class TestWhoPreparesThem:
    """Открытку собирает каждая точка, где карточку заводят или правят."""

    def test_form_from_the_bot_is_prepared(self):
        """Форма приходит от бота через сервис — с ней сразу и карточка для чата."""
        form = add_form(
            number=Number.SINGULAR, arabic="بَاب", translation_ru="дверь", image=picture()
        )

        assert postcard_url(form) is not None
        assert len(ready()) == 1

    def test_phrase_from_the_bot_is_prepared(self):
        """Фраза от бота — тем же путём."""
        phrase = add_phrase(arabic="مَرْحَبًا", translation_ru="привет", image=picture())

        assert postcard_url(phrase) is not None
        assert len(ready()) == 1

    def test_form_added_in_admin_is_prepared(self, admin_client):
        """Слово с формой завели руками в админке — карточка для чата собрана и тут."""
        answer = admin_client.post(
            "/admin/vocabulary/word/add/",
            {
                "themes": ["numbers"],
                "forms-TOTAL_FORMS": "1",
                "forms-INITIAL_FORMS": "0",
                "forms-MIN_NUM_FORMS": "0",
                "forms-MAX_NUM_FORMS": "2",
                "forms-0-number": str(Number.SINGULAR),
                "forms-0-arabic": "شَمْس",
                "forms-0-translation_ru": "солнце",
                "forms-0-transliteration": "",
                "forms-0-image": picture(),
            },
        )

        assert answer.status_code == status.HTTP_302_FOUND
        assert len(ready()) == 1

    def test_phrase_added_in_admin_is_prepared(self, admin_client):
        """Фраза из админки — тоже с карточкой для чата."""
        answer = admin_client.post(
            "/admin/vocabulary/phrase/add/",
            {
                "themes": ["greetings"],
                "arabic": "صَبَاح الخَيْر",
                "translation_ru": "доброе утро",
                "transliteration": "",
                "image": picture(),
            },
        )

        assert answer.status_code == status.HTTP_302_FOUND
        assert len(ready()) == 1

    def test_text_edited_in_admin_is_prepared_again(self, admin_client, phrase):
        """Правка перевода в админке пересобирает карточку: на ней нарисован этот текст."""
        phrase.image.save("probe.png", picture(), save=True)
        refresh_pictures(phrase)
        before = postcard_url(phrase)

        answer = admin_client.post(
            f"/admin/vocabulary/phrase/{phrase.pk}/change/",
            {
                "themes": phrase.themes,
                "arabic": phrase.arabic,
                "translation_ru": "здравствуй",
                "transliteration": "",
            },
        )
        phrase.refresh_from_db()

        assert answer.status_code == status.HTTP_302_FOUND
        assert postcard_url(phrase) != before
        assert len(ready()) == 2
