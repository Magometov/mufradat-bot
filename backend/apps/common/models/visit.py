from django.db import models
from django.utils.timezone import localtime

from apps.common.constants import BLANK_AND_NULL, Source
from apps.common.models.base import BaseModel


class Visit(BaseModel):
    """Один вход в приложение — строка на каждый заход, а не на человека."""

    source = models.CharField("Источник", max_length=16, choices=Source.choices)
    # Пусто у неопознанных: журнал пишет заход, а не сеанс.
    learner = models.ForeignKey(
        "common.Learner",
        verbose_name="Человек",
        related_name="visits",
        on_delete=models.CASCADE,
        **BLANK_AND_NULL,
    )
    user_agent = models.TextField("Браузер", blank=True, default="")

    class Meta(BaseModel.Meta):
        verbose_name = "Вход"
        verbose_name_plural = "Входы"

    def __str__(self) -> str:
        who = str(self.learner) if self.learner_id else self.get_source_display()

        return f"{who} — {localtime(self.created_at):%d.%m.%Y %H:%M}"
