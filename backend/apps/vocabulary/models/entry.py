from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.vocabulary.themes import Theme


class Entry(models.Model):
    """Слово — то, что учится карточкой."""

    arabic = models.TextField("Арабское", help_text="С огласовками")
    translation_ru = models.TextField("Перевод")
    transliteration = models.TextField("Транслитерация", blank=True, default="")
    image = models.ImageField("Картинка", upload_to="entries/", blank=True, null=True)
    themes = ArrayField(
        models.CharField(max_length=32, choices=Theme.choices),
        verbose_name="Темы",
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField("Добавлено", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        constraints = [
            models.UniqueConstraint(
                fields=["arabic", "translation_ru"],
                name="uq_entry_arabic_translation",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.arabic} — {self.translation_ru}"
