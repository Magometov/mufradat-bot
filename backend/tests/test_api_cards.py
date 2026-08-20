"""Ручки добавления формы и фразы: что заводится, что отбивается и кого пускают."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.vocabulary.constants import Number, Theme
from apps.vocabulary.models import Phrase, Word, WordForm

FORMS = "/api/v1/internal/forms/"
PHRASES = "/api/v1/internal/phrases/"

TOKEN = "bot-secret"


def picture() -> SimpleUploadedFile:
    """Картинка, какую бот прикладывает к карточке."""
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")

    return SimpleUploadedFile("probe.png", buffer.getvalue(), content_type="image/png")


def send(client: APIClient, url: str, fields: dict, *, token: str = TOKEN):
    """Добавление карточки: бот присылает поля формой, секрет — заголовком."""
    headers = {HEADER: token} if token else {}

    return client.post(url, fields, headers=headers)


@pytest.mark.django_db
class TestCardCreation:
    """Форма и фраза из бота заводятся в разделе «Новое в колоде»."""

    @pytest.fixture(autouse=True)
    def bot_token(self, settings) -> None:
        """Секрет бота задаёт тест: с пустым ручки не пустили бы никого."""
        settings.BOT_API_TOKEN = TOKEN

    def test_form_without_word_starts_a_new_one_in_the_lesson(
        self, client, django_assert_num_queries
    ):
        """Форма без слова заводит слово — сразу в разделе последнего урока."""
        fields = {"number": Number.SINGULAR, "arabic": "بَيْت", "translation_ru": "дом"}

        with django_assert_num_queries(5):
            answer = send(client, FORMS, fields)

        form = WordForm.objects.get()

        assert answer.status_code == status.HTTP_201_CREATED
        assert answer.json() == {"word": form.word_id}
        assert form.word.themes == [Theme.LAST_LESSON]
        assert (form.number, form.arabic, form.transliteration) == (Number.SINGULAR, "بَيْت", "")

    def test_form_joins_the_word_it_is_given(self, client, form, django_assert_num_queries):
        """С указанным словом новое не заводится, а темы слова остаются как были."""
        fields = {
            "word": form.word_id,
            "number": Number.PLURAL,
            "arabic": "كُتُب",
            "translation_ru": "книги",
        }

        with django_assert_num_queries(6):
            answer = send(client, FORMS, fields)

        assert answer.status_code == status.HTTP_201_CREATED
        assert answer.json() == {"word": form.word_id}
        assert Word.objects.count() == 1
        assert form.word.forms.count() == 2
        assert form.word.themes == ["numbers"]

    def test_same_writing_is_refused(self, client, form, django_assert_num_queries):
        """Одна и та же пара «арабское — перевод» второй раз в колоду не кладётся."""
        fields = {
            "number": Number.PLURAL,
            "arabic": form.arabic,
            "translation_ru": form.translation_ru,
        }

        with django_assert_num_queries(1):
            answer = send(client, FORMS, fields)

        assert answer.status_code == status.HTTP_409_CONFLICT
        assert answer.json() == {"detail": "уже в колоде"}
        assert WordForm.objects.count() == 1

    def test_second_form_with_the_same_number_is_refused(
        self, client, form, django_assert_num_queries
    ):
        """Число у слова одно на форму: вторая такая же упала бы на ограничении базы."""
        fields = {
            "word": form.word_id,
            "number": form.number,
            "arabic": "كِتَابٌ",
            "translation_ru": "книга (другая)",
        }

        with django_assert_num_queries(3):
            answer = send(client, FORMS, fields)

        assert answer.status_code == status.HTTP_409_CONFLICT
        assert answer.json() == {"detail": "у слова уже есть это число"}
        assert form.word.forms.count() == 1

    def test_picture_is_stored_under_the_card_number(self, client):
        """Картинка кладётся под номером карточки: `w12.webp` понятнее случайного имени."""
        fields = {
            "number": Number.SINGULAR,
            "arabic": "شَمْس",
            "translation_ru": "солнце",
            "image": picture(),
        }

        answer = send(client, FORMS, fields)

        form = WordForm.objects.get()

        assert answer.status_code == status.HTTP_201_CREATED
        assert form.image.name == f"cards/w{form.pk}.webp"

    def test_phrase_starts_in_the_lesson_too(self, client, django_assert_num_queries):
        """Фраза заводится там же и отвечает своим номером."""
        fields = {"arabic": "صَبَاح الخَيْر", "translation_ru": "доброе утро"}

        with django_assert_num_queries(4):
            answer = send(client, PHRASES, fields)

        phrase = Phrase.objects.get()

        assert answer.status_code == status.HTTP_201_CREATED
        assert answer.json() == {"phrase": phrase.pk}
        assert phrase.themes == [Theme.LAST_LESSON]

    def test_same_phrase_is_refused(self, client, phrase, django_assert_num_queries):
        """Фраза-повтор отбивается так же, как форма слова."""
        fields = {"arabic": phrase.arabic, "translation_ru": phrase.translation_ru}

        with django_assert_num_queries(1):
            answer = send(client, PHRASES, fields)

        assert answer.status_code == status.HTTP_409_CONFLICT
        assert Phrase.objects.count() == 1

    def test_form_without_writing_is_rejected(self, client, django_assert_num_queries):
        """Без арабского карточки не бывает: до базы дело не доходит."""
        with django_assert_num_queries(0):
            answer = send(client, FORMS, {"number": Number.SINGULAR, "translation_ru": "дом"})

        assert answer.status_code == status.HTTP_400_BAD_REQUEST
        assert WordForm.objects.count() == 0

    @pytest.mark.parametrize("url", [FORMS, PHRASES])
    def test_stranger_cannot_add_anything(self, client, url, django_assert_num_queries):
        """Без секрета ручки не отвечают: колода наружу не открыта."""
        fields = {"arabic": "شَيْء", "translation_ru": "вещь", "number": Number.SINGULAR}

        with django_assert_num_queries(0):
            answer = send(client, url, fields, token="")

        assert answer.status_code == status.HTTP_403_FORBIDDEN
        assert WordForm.objects.count() == 0
        assert Phrase.objects.count() == 0
