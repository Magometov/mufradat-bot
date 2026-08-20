"""Журнал входов: связь с человеком и молчание про владельца."""

import pytest
from django.test import override_settings

from apps.common.constants import Source
from apps.common.models import Visit
from apps.common.services import identify, log

OWNER = 900
STRANGER = 901


@pytest.mark.django_db
class TestVisitLog:
    """Запись о заходе: кому принадлежит, что в неё попадает и когда её нет."""

    def test_visit_points_at_learner(self):
        """Заход из Telegram ссылается на человека, а не хранит его id у себя."""
        learner = identify(telegram_id=STRANGER, username="ali")

        log(source=Source.TELEGRAM, learner=learner, user_agent="Mozilla/5.0")

        visit = Visit.objects.get()

        assert visit.learner_id == learner.pk
        assert visit.source == Source.TELEGRAM

    def test_site_visit_has_no_learner(self):
        """Заход с сайта — без ссылки: в этот момент мы не знаем, кто пришёл."""
        log(source=Source.SITE, user_agent="Mozilla/5.0")

        assert Visit.objects.get().learner_id is None

    @override_settings(ADMIN_TELEGRAM_ID=OWNER)
    def test_owner_visit_is_not_logged_but_learner_stays(self):
        """Владельца журнал не пишет, а запись о человеке остаётся: к ней привязан прогресс."""
        owner = identify(telegram_id=OWNER, username="me")

        log(source=Source.TELEGRAM, learner=owner)

        assert Visit.objects.count() == 0
        assert owner.pk is not None

    def test_user_agent_is_trimmed(self):
        """Строка браузера обрезается, чтобы запись не пухла."""
        log(source=Source.SITE, user_agent="x" * 900)

        assert len(Visit.objects.get().user_agent) == 400

    def test_deleting_learner_takes_visits_with_it(self):
        """Удалили человека — его заходы уходят следом: журнал без человека нечитаем."""
        learner = identify(telegram_id=STRANGER)
        log(source=Source.TELEGRAM, learner=learner)

        learner.delete()

        assert Visit.objects.count() == 0
