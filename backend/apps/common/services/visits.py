"""Журнал входов."""

from django.conf import settings

from apps.common.constants import USER_AGENT_LENGTH, Source
from apps.common.models import Learner, Visit


def log(*, source: Source, learner: Learner | None = None, user_agent: str = "") -> None:
    """Пишет вход. Владельца не пишет: его заходы мешают считать чужие."""
    if learner is not None and learner.telegram_id == settings.ADMIN_TELEGRAM_ID:
        return

    Visit.objects.create(
        source=source,
        learner=learner,
        user_agent=user_agent[:USER_AGENT_LENGTH],
    )
