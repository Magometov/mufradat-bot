"""Модель человека и опознание по Telegram id."""

import pytest
from django.db import IntegrityError, transaction

from apps.common.constants import Source
from apps.common.models import Learner
from apps.common.services import identify, visitor


@pytest.mark.django_db
class TestIdentify:
    """Опознание по Telegram id: запись одна на человека, ник следует за Telegram."""

    def test_telegram_learner_is_created_once(self):
        """Второй заход того же человека новую запись не заводит."""
        first = identify(telegram_id=111, username="ali")
        second = identify(telegram_id=111, username="ali")

        assert first.pk == second.pk
        assert Learner.objects.count() == 1

    def test_username_follows_telegram(self):
        """Сменившийся ник переписывается: он один на человека, а не снимок на заход."""
        identify(telegram_id=222, username="old")
        learner = identify(telegram_id=222, username="new")

        assert learner.username == "new"

    def test_empty_username_does_not_erase_saved_one(self):
        """Заход без ника не стирает известный: Telegram отдаёт ник не всегда."""
        identify(telegram_id=333, username="ali")
        learner = identify(telegram_id=333)

        assert learner.username == "ali"


@pytest.mark.django_db
class TestLearner:
    """Сама запись: чем человек опознаётся и как подписывается в админке."""

    def test_learner_without_identity_is_rejected(self):
        """Без Telegram id и без ключа запись мусорная: найти её потом нечем."""
        with pytest.raises(IntegrityError), transaction.atomic():
            Learner.objects.create()

    def test_str_prefers_username(self):
        """Подпись в админке: ник, а иначе id, а у гостя — номер."""
        assert str(identify(telegram_id=444, username="ali")) == "@ali"
        assert str(identify(telegram_id=555)) == "555"
        assert str(Learner.objects.create(key_hash="a" * 64)).startswith("гость №")


@pytest.mark.django_db
class TestVisitor:
    """Кого пускать за человека: подпись Telegram, секрет бота или никто."""

    def test_visitor_without_signature_is_nobody(self):
        """Заход без подписи — сайт и никто: заводить человека не на что."""
        assert visitor() == (Source.SITE, None)

    def test_visitor_does_not_trust_the_body(self):
        """Названный в теле id без секрета бота ничего не значит: ручка открыта наружу."""
        source, learner = visitor(telegram_id=666, username="fake")

        assert (source, learner) == (Source.SITE, None)
        assert Learner.objects.count() == 0

    def test_visitor_trusts_the_bot(self):
        """Боту верим: у него подписи нет, зато есть общий секрет."""
        source, learner = visitor(telegram_id=777, username="ali", is_bot=True)

        assert source == Source.TELEGRAM
        assert learner.telegram_id == 777
