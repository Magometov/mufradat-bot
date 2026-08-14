from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.vocabulary.models.card import Card
from apps.vocabulary.themes import Theme


class Phrase(Card):
    """Фраза. Форм нет: числа у фразы не бывает."""

    themes = ArrayField(
        models.CharField(max_length=32, choices=Theme.choices),
        verbose_name="Темы",
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField("Добавлено", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Фраза"
        verbose_name_plural = "Фразы"
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=["arabic", "translation_ru"],
                name="uq_phrase_arabic_translation",
            ),
        ]
