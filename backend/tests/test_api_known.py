"""Ручка «что уже в колоде»: ею бот отсеивает повторы до того, как рисовать картинки."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.internal.permissions import HEADER

URL = "/api/v1/internal/known/"

TOKEN = "bot-secret"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def ask(client: APIClient, pairs: list[tuple[str, str]], *, token: str = TOKEN):
    """Спрашивает про пачку пар «арабское — перевод»."""
    headers = {HEADER: token} if token else {}
    cards = [{"arabic": arabic, "translation_ru": translation} for arabic, translation in pairs]

    return client.post(URL, {"cards": cards}, format="json", headers=headers)


@pytest.mark.django_db
class TestKnownCards:
    """Что из присланного уже лежит в колоде: и формы слов, и фразы."""

    @pytest.fixture(autouse=True)
    def bot_token(self, settings) -> None:
        """Секрет бота задаёт тест: с пустым ручка не пустила бы никого."""
        settings.BOT_API_TOKEN = TOKEN

    def test_known_cards_come_back_in_the_order_asked(
        self, client, form, phrase, django_assert_num_queries
    ):
        """В ответе только те пары, что в колоде, и в том же порядке, в каком спросили."""
        fresh = ("شَمْس", "солнце")

        with django_assert_num_queries(2):
            answer = ask(
                client,
                [
                    (phrase.arabic, phrase.translation_ru),
                    fresh,
                    (form.arabic, form.translation_ru),
                ],
            )

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {
            "known": [
                {"arabic": phrase.arabic, "translation_ru": phrase.translation_ru},
                {"arabic": form.arabic, "translation_ru": form.translation_ru},
            ]
        }

    def test_halves_of_different_cards_are_not_a_match(self, client, form, phrase):
        """Арабское от одной карточки с переводом от другой в колоде не лежит."""
        answer = ask(client, [(form.arabic, phrase.translation_ru)])

        assert answer.json() == {"known": []}

    def test_nothing_known_is_an_empty_list(self, client, django_assert_num_queries):
        """Колода пуста — пустой список, а не отказ."""
        with django_assert_num_queries(2):
            answer = ask(client, [("قَلَم", "ручка")])

        assert answer.status_code == status.HTTP_200_OK
        assert answer.json() == {"known": []}

    def test_empty_body_is_rejected(self, client, django_assert_num_queries):
        """Спрашивать не о чем — это ошибка запроса, а не пустой ответ."""
        with django_assert_num_queries(0):
            answer = ask(client, [])

        assert answer.status_code == status.HTTP_400_BAD_REQUEST

    def test_stranger_gets_nothing(self, client, form, django_assert_num_queries):
        """Служебная ручка: без секрета до колоды дело не доходит."""
        with django_assert_num_queries(0):
            answer = ask(client, [(form.arabic, form.translation_ru)], token="")

        assert answer.status_code == status.HTTP_403_FORBIDDEN
