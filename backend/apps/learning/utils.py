"""Проверки, которым база не нужна."""

from datetime import datetime

from django.conf import settings
from django.utils.timezone import localtime

from apps.common.models import Learner
from apps.learning.constants import AWAKE_FROM, AWAKE_TO, GROUP_HOURS


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


def group_slot(now: datetime) -> datetime | None:
    """Начало слота рассылки в группу, в который попало время. `None` — до первого слота.

    Слот, а не «прошёл ли час»: за границу суток он переходит сам, и опрос ручки хоть
    каждую минуту второго сообщения не даёт.
    """
    local = localtime(now)
    started = [hour for hour in GROUP_HOURS if hour <= local.hour]

    if not started:
        return None

    return local.replace(hour=max(started), minute=0, second=0, microsecond=0)
