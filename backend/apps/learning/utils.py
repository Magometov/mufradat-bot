"""Проверки, которым база не нужна."""

from datetime import datetime

from django.conf import settings
from django.utils.timezone import localtime

from apps.common.models import Learner
from apps.learning.constants import AWAKE_FROM, AWAKE_TO


def enabled(learner: Learner | None) -> bool:
    """Видит ли человек новую логику.

    Без опознания — нет: оценки принимает только ручка с человеком, и включённая логика
    без него дала бы сеанс, который ничего не сохраняет.
    """
    if learner is None:
        return False

    return settings.SCHEDULING_FOR_ALL or (learner.telegram_id is not None and learner.scheduling)


def is_awake(now: datetime) -> bool:
    """Попадает ли время в окно, когда бот пишет. Вне его — тишина."""
    hour = localtime(now).hour

    return AWAKE_FROM <= hour < AWAKE_TO
