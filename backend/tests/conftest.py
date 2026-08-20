"""Общие заготовки для тестов."""

import pytest

from apps.common.models import Learner
from apps.vocabulary.models import Phrase, Word, WordForm

# Клиент ручек — общий на все файлы, поэтому живёт отдельно.
pytest_plugins = ["tests.fixtures.api"]


@pytest.fixture(autouse=True)
def media(tmp_path, settings) -> None:
    """Картинки тестов не оседают в рабочем каталоге."""
    settings.MEDIA_ROOT = tmp_path


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
