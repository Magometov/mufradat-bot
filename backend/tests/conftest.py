"""Общие заготовки для тестов."""

import pytest

from apps.common.models import Learner
from apps.vocabulary.models import Phrase, Word, WordForm


@pytest.fixture
def learner(db) -> Learner:
    return Learner.objects.create(telegram_id=1001, username="ali")


@pytest.fixture
def form(db) -> WordForm:
    word = Word.objects.create(themes=["numbers"])

    return WordForm.objects.create(word=word, number=1, arabic="كِتَاب", translation_ru="книга")


@pytest.fixture
def phrase(db) -> Phrase:
    return Phrase.objects.create(themes=["greetings"], arabic="مَرْحَبًا", translation_ru="привет")
