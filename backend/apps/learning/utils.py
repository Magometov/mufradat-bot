"""Проверки, которым база не нужна."""

from django.conf import settings

from apps.common.models import Learner


def enabled(learner: Learner | None) -> bool:
    """Видит ли человек новую логику.

    Без опознания — нет: оценки принимает только ручка с человеком, и включённая логика
    без него дала бы сеанс, который ничего не сохраняет.
    """
    if learner is None:
        return False

    return settings.SCHEDULING_FOR_ALL or (learner.telegram_id is not None and learner.scheduling)
