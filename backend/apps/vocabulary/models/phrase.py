from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.common.models import BaseModel
from apps.vocabulary.constants import Theme
from apps.vocabulary.models.base import Card


class Phrase(Card, BaseModel):
    """Фраза. Форм нет: числа у фразы не бывает."""

    themes = ArrayField(
        models.CharField(max_length=32, choices=Theme.choices),
        verbose_name="Темы",
        default=list,
        blank=True,
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Фраза"
        verbose_name_plural = "Фразы"
        constraints = [
            models.UniqueConstraint(
                fields=["arabic", "translation_ru"],
                name="uq_phrase_arabic_translation",
            ),
        ]
