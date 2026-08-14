"""Журнал входов."""

from django.conf import settings

from apps.common.constants import USER_AGENT_LENGTH, Source
from apps.common.models import Visit


def log(
    *,
    source: Source,
    telegram_id: int | None = None,
    username: str = "",
    user_agent: str = "",
) -> None:
    """Пишет вход. Владельца не пишет: его заходы мешают считать чужие."""
    if telegram_id is not None and telegram_id == settings.ADMIN_TELEGRAM_ID:
        return

    Visit.objects.create(
        source=source,
        telegram_id=telegram_id,
        username=username,
        user_agent=user_agent[:USER_AGENT_LENGTH],
    )
