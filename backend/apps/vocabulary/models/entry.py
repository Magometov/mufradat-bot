from django.db import models

from apps.vocabulary.enums import Kind, Source
from apps.vocabulary.services.arabic import normalize_arabic


class Entry(models.Model):
    """Единица заучивания: слово или фраза."""

    kind = models.CharField("Тип", max_length=8, choices=Kind)
    arabic = models.TextField("Арабское", help_text="С огласовками, как распознано")
    arabic_norm = models.TextField("Ключ поиска похожих", editable=False, db_index=True)
    translation_ru = models.TextField("Перевод")
    transliteration = models.TextField("Транслитерация", blank=True, default="")
    topic = models.TextField("Тема", blank=True, default="", db_index=True)
    source = models.CharField("Источник", max_length=16, choices=Source)
    created_at = models.DateTimeField("Добавлено", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Единица"
        verbose_name_plural = "Единицы"
        constraints = [
            models.UniqueConstraint(
                fields=["arabic", "translation_ru"],
                name="uq_entry_arabic_translation",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.arabic} — {self.translation_ru}"

    def save(self, *args: object, **kwargs: object) -> None:
        self.arabic_norm = normalize_arabic(self.arabic)
        super().save(*args, **kwargs)
