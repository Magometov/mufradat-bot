"""Слово в группу: пора ли отправлять и какое слово взять."""

from datetime import datetime
from random import choice

from django.conf import settings
from django.db.models import Max
from django.utils import timezone

from apps.learning.models import GroupPost
from apps.learning.queryset import link, unsent_words
from apps.learning.utils import group_slot
from apps.vocabulary.models import WordForm


def _slot_is_open(now: datetime) -> bool:
    """Наступил ли слот, в который ещё не отправляли."""
    slot = group_slot(now)

    if slot is None:
        return False

    last = GroupPost.objects.aggregate(at=Max("sent_at"))["at"]

    return last is None or last < slot


def _first_circle(now: datetime) -> WordForm | None:
    """Случайное слово из тех, что ещё не уезжали.

    Колода поднимается в память целиком: она в сотни карточек, а спрашивают её дважды
    в день. Станет тысячи — считать случайную выборку в базе.
    """
    fresh = list(unsent_words())

    if not fresh:
        return None

    card = choice(fresh)
    GroupPost.objects.create(**link(card), sent_at=now)

    return card


def _next_circle(now: datetime) -> WordForm | None:
    """Колода пройдена: дальше идут слова, отправленные раньше всех."""
    post = GroupPost.objects.words().by_age().first()

    if post is None:
        return None

    post.sent_at = now
    post.save(update_fields=["sent_at"])

    return post.form


def take_group_card(*, now: datetime | None = None, forced: bool = False) -> WordForm | None:
    """Слово для группы. Помечает отправку, поэтому за слот отдаёт его только раз.

    `forced` — просьба прислать слово сейчас: слот не смотрим, но круг колоды двигаем,
    иначе присланное вручную вернулось бы вторым заходом.
    """
    now = now or timezone.now()

    # Без группы отправлять некуда, и колоду жечь незачем: слова остались бы
    # помеченными, а в чат не пришло ни одного.
    if not settings.GROUP_CHAT_ID:
        return None

    if not forced and not _slot_is_open(now):
        return None

    return _first_circle(now) or _next_circle(now)
