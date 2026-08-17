"""Проверки, которым база не нужна."""

from django.conf import settings

from apps.common.models import Learner


def enabled(learner: Learner | None) -> bool:
    """Видит ли человек новую логику: по галочке в админке и только в Telegram."""
    if settings.SCHEDULING_FOR_ALL:
        return True

    return learner is not None and learner.telegram_id is not None and learner.scheduling
