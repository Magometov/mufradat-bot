"""Модель человека и опознание по Telegram id."""

import pytest
from django.db import IntegrityError, transaction

from apps.common.models import Learner
from apps.common.services import learners


@pytest.mark.django_db
def test_telegram_learner_is_created_once():
    """Второй заход того же человека новую запись не заводит."""
    first = learners.identify(telegram_id=111, username="ali")
    second = learners.identify(telegram_id=111, username="ali")

    assert first.pk == second.pk
    assert Learner.objects.count() == 1


@pytest.mark.django_db
def test_username_follows_telegram():
    """Сменившийся ник переписывается: он один на человека, а не снимок на заход."""
    learners.identify(telegram_id=222, username="old")
    learner = learners.identify(telegram_id=222, username="new")

    assert learner.username == "new"


@pytest.mark.django_db
def test_empty_username_does_not_erase_saved_one():
    """Заход без ника не стирает известный: Telegram отдаёт ник не всегда."""
    learners.identify(telegram_id=333, username="ali")
    learner = learners.identify(telegram_id=333)

    assert learner.username == "ali"


@pytest.mark.django_db
def test_learner_without_identity_is_rejected():
    """Без Telegram id и без ключа запись мусорная: найти её потом нечем."""
    with pytest.raises(IntegrityError), transaction.atomic():
        Learner.objects.create()


@pytest.mark.django_db
def test_str_prefers_username():
    """Подпись в админке: ник, а иначе id, а у гостя — номер."""
    assert str(learners.identify(telegram_id=444, username="ali")) == "@ali"
    assert str(learners.identify(telegram_id=555)) == "555"
    assert str(Learner.objects.create(key_hash="a" * 64)).startswith("гость №")
