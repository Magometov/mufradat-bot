"""Ручки раздела урока: что бот в нём видит и как разбирает по темам."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER
from apps.vocabulary.constants import Number, Theme
from apps.vocabulary.models import Phrase, Word, WordForm

LESSON = "/api/v1/internal/lesson/"
MOVE = "/api/v1/internal/lesson/move/"

TOKEN = "bot-secret"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def lesson_word(*, forms: dict[int, str] | None = None) -> Word:
    """Слово в разделе последнего урока с переводами по числам."""
    word = Word.objects.create(themes=[Theme.LAST_LESSON])

    for number, translation in (forms or {}).items():
        WordForm.objects.create(
            word=word, number=number, arabic=f"a{number}{word.pk}", translation_ru=translation
        )

    return word


@pytest.mark.django_db
class TestLesson:
    """Раздел урока: список для бота и разбор единиц по темам."""

    @pytest.fixture(autouse=True)
    def bot_token(self, settings) -> None:
        """Секрет бота задаёт тест: с пустым ручки не пустили бы никого."""
        settings.BOT_API_TOKEN = TOKEN

    def test_lesson_lists_only_its_own_units(self, client, form, django_assert_num_queries):
        """В списке — слова и фразы раздела урока; чужие темы в него не попадают."""
        word = lesson_word(forms={Number.SINGULAR: "книга", Number.PLURAL: "книги"})
        phrase = Phrase.objects.create(
            themes=[Theme.LAST_LESSON], arabic="سَلَام", translation_ru="мир"
        )

        with django_assert_num_queries(3):
            answer = client.get(LESSON, headers={HEADER: TOKEN})

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json()["units"] == [
            {"kind": "word", "id": word.pk, "title": "книга / книги"},
            {"kind": "phrase", "id": phrase.pk, "title": "мир"},
        ]

    def test_lesson_offers_every_theme_but_itself(self, client, django_assert_num_queries):
        """Разбирают по темам колоды: сам раздел урока целью не бывает."""
        with django_assert_num_queries(2):
            themes = client.get(LESSON, headers={HEADER: TOKEN}).json()["themes"]

        assert {"slug": "numbers", "name": "Цифры"} in themes
        assert Theme.LAST_LESSON.value not in [theme["slug"] for theme in themes]

    def test_word_without_forms_still_has_a_title(self, client):
        """Слово без форм подписывается собой: пустой строки бот не получит."""
        word = lesson_word()

        units = client.get(LESSON, headers={HEADER: TOKEN}).json()["units"]

        assert units == [{"kind": "word", "id": word.pk, "title": str(word)}]

    def test_move_takes_the_word_out_of_the_lesson(self, client, django_assert_num_queries):
        """Разбор снимает раздел урока и ставит выбранные темы."""
        word = lesson_word(forms={Number.SINGULAR: "дом"})
        move = {"kind": "word", "id": word.pk, "themes": ["family"]}

        with django_assert_num_queries(2):
            answer = client.post(MOVE, move, format="json", headers={HEADER: TOKEN})

        word.refresh_from_db()

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {"themes": ["family"]}
        assert word.themes == ["family"]

    def test_move_keeps_the_themes_it_did_not_touch(self, client):
        """Прочие темы слова остаются: разбор снимает только раздел урока."""
        word = Word.objects.create(themes=[Theme.LAST_LESSON, "numbers"])

        answer = client.post(
            MOVE,
            {"kind": "word", "id": word.pk, "themes": ["family"]},
            format="json",
            headers={HEADER: TOKEN},
        )

        assert answer.json() == {"themes": ["numbers", "family"]}

    def test_move_without_themes_leaves_the_phrase_bare(self, client, phrase):
        """Пустой список — единица уходит из урока вообще без темы."""
        phrase.themes = [Theme.LAST_LESSON]
        phrase.save(update_fields=["themes"])

        answer = client.post(
            MOVE,
            {"kind": "phrase", "id": phrase.pk, "themes": []},
            format="json",
            headers={HEADER: TOKEN},
        )
        phrase.refresh_from_db()

        assert answer.json() == {"themes": []}
        assert phrase.themes == []

    def test_move_into_the_lesson_itself_is_rejected(self, client, django_assert_num_queries):
        """Раздел урока не цель разбора: такую тему ручка не принимает."""
        word = lesson_word()

        with django_assert_num_queries(0):
            answer = client.post(
                MOVE,
                {"kind": "word", "id": word.pk, "themes": [Theme.LAST_LESSON]},
                format="json",
                headers={HEADER: TOKEN},
            )

        word.refresh_from_db()

        assert answer.status_code == status.HTTP_400_BAD_REQUEST
        assert word.themes == [Theme.LAST_LESSON]

    def test_move_of_unknown_unit_is_not_found(self, client, django_assert_num_queries):
        """Единицы нет — четыреста четыре, а не пятисотая."""
        with django_assert_num_queries(1):
            answer = client.post(
                MOVE,
                {"kind": "word", "id": 10**6, "themes": ["family"]},
                format="json",
                headers={HEADER: TOKEN},
            )

        assert answer.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("url", [LESSON, MOVE])
    def test_stranger_sees_no_lesson(self, client, url, django_assert_num_queries):
        """Раздел урока — служебная ручка: без секрета не отвечает."""
        with django_assert_num_queries(0):
            answer = client.post(url, headers={HEADER: "wrong"})

        assert answer.status_code == status.HTTP_403_FORBIDDEN
