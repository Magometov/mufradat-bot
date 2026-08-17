"""Модель человека и опознание по Telegram id."""

import pytest
from django.db import IntegrityError, transaction
from django.test import override_settings

from apps.common.constants import Source
from apps.common.models import Learner
from apps.common.services import identify, visitor


@pytest.mark.django_db
def test_telegram_learner_is_created_once():
    """Второй заход того же человека новую запись не заводит."""
    first = identify(telegram_id=111, username="ali")
    second = identify(telegram_id=111, username="ali")

    assert first.pk == second.pk
    assert Learner.objects.count() == 1


@pytest.mark.django_db
def test_username_follows_telegram():
    """Сменившийся ник переписывается: он один на человека, а не снимок на заход."""
    identify(telegram_id=222, username="old")
    learner = identify(telegram_id=222, username="new")

    assert learner.username == "new"


@pytest.mark.django_db
def test_empty_username_does_not_erase_saved_one():
    """Заход без ника не стирает известный: Telegram отдаёт ник не всегда."""
    identify(telegram_id=333, username="ali")
    learner = identify(telegram_id=333)

    assert learner.username == "ali"


@pytest.mark.django_db
def test_learner_without_identity_is_rejected():
    """Без Telegram id и без ключа запись мусорная: найти её потом нечем."""
    with pytest.raises(IntegrityError), transaction.atomic():
        Learner.objects.create()


@pytest.mark.django_db
def test_str_prefers_username():
    """Подпись в админке: ник, а иначе id, а у гостя — номер."""
    assert str(identify(telegram_id=444, username="ali")) == "@ali"
    assert str(identify(telegram_id=555)) == "555"
    assert str(Learner.objects.create(key_hash="a" * 64)).startswith("гость №")


@pytest.mark.django_db
def test_visitor_without_signature_is_nobody():
    """Заход без подписи — сайт и никто: заводить человека не на что."""
    assert visitor() == (Source.SITE, None)


@pytest.mark.django_db
def test_visitor_does_not_trust_the_body():
    """Названный в теле id без секрета бота ничего не значит: ручка открыта наружу."""
    source, learner = visitor(telegram_id=666, username="fake")

    assert (source, learner) == (Source.SITE, None)
    assert Learner.objects.count() == 0


@pytest.mark.django_db
def test_visitor_trusts_the_bot():
    """Боту верим: у него подписи нет, зато есть общий секрет."""
    source, learner = visitor(telegram_id=777, username="ali", is_bot=True)

    assert source == Source.TELEGRAM
    assert learner.telegram_id == 777


@override_settings(DEBUG=True, SCHEDULING_FOR_ALL=True)
@pytest.mark.django_db
def test_local_learner_appears_only_in_development():
    """На своей машине неопознанный получает локального человека."""
    source, learner = visitor()

    assert source == Source.SITE
    assert learner is not None
    assert learner.telegram_id is None


@override_settings(DEBUG=False, SCHEDULING_FOR_ALL=True)
@pytest.mark.django_db
def test_local_learner_never_appears_in_production():
    """Без DEBUG эта ветка мертва, даже когда логика открыта всем."""
    assert visitor() == (Source.SITE, None)
    assert Learner.objects.count() == 0
