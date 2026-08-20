"""Поиск по колоде: что находится по русскому слову и в каком порядке."""

import pytest

from apps.vocabulary.models import Phrase, Word, WordForm
from apps.vocabulary.services import find


def add_word(translation: str, *, arabic: str = "كَلِمَة") -> WordForm:
    """Ещё одно слово в колоде."""
    word = Word.objects.create(themes=["nouns"])

    return WordForm.objects.create(word=word, number=1, arabic=arabic, translation_ru=translation)


@pytest.fixture
def deck(db) -> list[WordForm]:
    """Три слова с непересекающимися переводами."""
    return [add_word("машина"), add_word("дом"), add_word("книга")]


@pytest.mark.django_db
class TestFind:
    """Поиск по колоде: по какому куску слова находит, в каком порядке и до какого потолка."""

    def test_word_is_found_by_its_translation(self, deck):
        """Слово ищется по переводу."""
        assert [card.translation_ru for card in find("машина", limit=10)] == ["машина"]

    def test_a_part_of_the_word_is_enough(self, deck):
        """Достаточно куска слова: инлайн спрашивает на каждой набранной букве."""
        assert [card.translation_ru for card in find("маш", limit=10)] == ["машина"]

    def test_case_does_not_matter(self, deck):
        """Регистр не важен: с большой буквы набирают так же часто."""
        assert [card.translation_ru for card in find("Машина", limit=10)] == ["машина"]

    def test_phrases_are_found_too(self, deck):
        """Фразы ищутся наравне со словами: колода одна."""
        Phrase.objects.create(themes=["greetings"], arabic="كَيْفَ حَالُك", translation_ru="Как дела?")

        assert [card.translation_ru for card in find("дела", limit=10)] == ["Как дела?"]

    def test_unknown_word_finds_nothing(self, deck):
        """Чего в колоде нет, того поиск не выдумывает."""
        assert find("самолёт", limit=10) == []

    def test_empty_query_shows_the_newest(self, deck):
        """Пустой запрос — свежее из колоды: `@бот` без слова показывает последнее."""
        assert find("", limit=2) == [deck[2], deck[1]]

    def test_limit_holds(self, deck):
        """Потолок соблюдается: у инлайна он свой, и превысить его нельзя."""
        assert len(find("", limit=1)) == 1

    def test_limit_holds_across_both_tables(self, deck):
        """Потолок общий на слова и фразы, а не по потолку на каждую таблицу."""
        Phrase.objects.create(themes=["greetings"], arabic="بَيْت كَبِير", translation_ru="большой дом")

        assert len(find("дом", limit=1)) == 1
