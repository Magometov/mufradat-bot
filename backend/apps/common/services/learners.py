"""Люди: кто пришёл и как его найти."""

from apps.common.constants import USERNAME_LENGTH, Source
from apps.common.models import Learner
from apps.common.utils import user_from


def identify(*, telegram_id: int, username: str = "") -> Learner:
    """Человек по Telegram id; нет такого — заводит. Пустой ник известный не стирает."""
    learner, created = Learner.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"username": username[:USERNAME_LENGTH]},
    )

    if not created and username and learner.username != username[:USERNAME_LENGTH]:
        learner.username = username[:USERNAME_LENGTH]
        learner.save(update_fields=["username"])

    return learner


def visitor(
    *,
    init_data: str = "",
    telegram_id: int | None = None,
    username: str = "",
    is_bot: bool = False,
) -> tuple[Source, Learner | None]:
    """Откуда заход и кто его сделал. Без опознания — сайт и никто."""
    signed_user = user_from(init_data)

    if signed_user is not None:
        return Source.TELEGRAM, identify(telegram_id=signed_user[0], username=signed_user[1])

    # Названному id верим только боту: у него подписи нет, зато есть общий секрет.
    if is_bot and telegram_id:
        return Source.TELEGRAM, identify(telegram_id=telegram_id, username=username)

    return Source.SITE, None
