from django.db import models

from apps.common.constants import BLANK_AND_NULL
from apps.common.models import BaseModel
from apps.learning.queryset import AnyCard, CardStateQuerySet, GroupPostQuerySet
from apps.vocabulary.models import Phrase, WordForm


class CardState(BaseModel):
    """Что человек помнит про одну карточку: уровень лестницы и когда показать снова."""

    learner = models.ForeignKey(
        "common.Learner",
        verbose_name="Человек",
        related_name="states",
        on_delete=models.CASCADE,
    )
    # Две ссылки вместо одной общей: так база сама подчистит состояния удалённых карточек.
    form = models.ForeignKey(
        WordForm,
        verbose_name="Форма",
        related_name="states",
        on_delete=models.CASCADE,
        **BLANK_AND_NULL,
    )
    phrase = models.ForeignKey(
        Phrase,
        verbose_name="Фраза",
        related_name="states",
        on_delete=models.CASCADE,
        **BLANK_AND_NULL,
    )
    level = models.PositiveSmallIntegerField("Уровень", default=0)
    step = models.PositiveSmallIntegerField("Верных подряд", default=0)
    lapses = models.PositiveSmallIntegerField("Промахов за жизнь", default=0)
    lapsed_from = models.PositiveSmallIntegerField("Упала с уровня", default=0)
    due_at = models.DateTimeField("Показать", db_index=True)
    answered_at = models.DateTimeField("Оценили", **BLANK_AND_NULL)
    reminded_at = models.DateTimeField("Отправляли в чат", **BLANK_AND_NULL)

    objects = CardStateQuerySet.as_manager()

    class Meta(BaseModel.Meta):
        verbose_name = "Состояние карточки"
        verbose_name_plural = "Состояния карточек"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(form__isnull=False, phrase__isnull=True)
                | models.Q(form__isnull=True, phrase__isnull=False),
                name="cardstate_one_card",
            ),
            models.UniqueConstraint(
                fields=["learner", "form"],
                name="uq_cardstate_learner_form",
            ),
            models.UniqueConstraint(
                fields=["learner", "phrase"],
                name="uq_cardstate_learner_phrase",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.card} — уровень {self.level}"

    @property
    def card(self) -> AnyCard:
        """Карточка, о которой это состояние."""
        return self.form or self.phrase


class GroupPost(BaseModel):
    """Карточка, уехавшая в группу. Строка на карточку: по ним колода идёт по кругу."""

    form = models.ForeignKey(
        WordForm,
        verbose_name="Форма",
        related_name="group_posts",
        on_delete=models.CASCADE,
        **BLANK_AND_NULL,
    )
    phrase = models.ForeignKey(
        Phrase,
        verbose_name="Фраза",
        related_name="group_posts",
        on_delete=models.CASCADE,
        **BLANK_AND_NULL,
    )
    sent_at = models.DateTimeField("Отправлено", db_index=True)

    objects = GroupPostQuerySet.as_manager()

    class Meta(BaseModel.Meta):
        verbose_name = "Слово в группе"
        verbose_name_plural = "Слова в группе"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(form__isnull=False, phrase__isnull=True)
                | models.Q(form__isnull=True, phrase__isnull=False),
                name="grouppost_one_card",
            ),
            models.UniqueConstraint(fields=["form"], name="uq_grouppost_form"),
            models.UniqueConstraint(fields=["phrase"], name="uq_grouppost_phrase"),
        ]

    def __str__(self) -> str:
        return f"{self.card} — {self.sent_at:%d.%m.%Y}"

    @property
    def card(self) -> AnyCard:
        """Карточка, которую отправляли."""
        return self.form or self.phrase
