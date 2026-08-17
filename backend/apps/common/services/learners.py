"""Люди: найти по Telegram id или завести."""

from apps.common.constants import USERNAME_LENGTH
from apps.common.models import Learner


def identify(*, telegram_id: int, username: str = "") -> Learner:
    """Человек по Telegram id; нет такого — заводит. Ник обновляет, если он сменился.

    Заводится здесь, а не в журнале входов: журнал намеренно не пишет владельца, а
    запись о человеке нужна и ему — иначе прогресс некуда привязать.
    """
    learner, created = Learner.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"username": username[:USERNAME_LENGTH]},
    )

    if not created and username and learner.username != username[:USERNAME_LENGTH]:
        learner.username = username[:USERNAME_LENGTH]
        learner.save(update_fields=["username"])

    return learner
