from django.db import models

from apps.vocabulary.enums import Kind


class Entry(models.Model):
    """Единица заучивания: слово или фраза."""

    kind = models.CharField("Тип", max_length=8, choices=Kind, default=Kind.WORD)
    arabic = models.TextField("Арабское", help_text="С огласовками")
    translation_ru = models.TextField("Перевод")
    transliteration = models.TextField("Транслитерация", blank=True, default="")
    image = models.ImageField("Картинка", upload_to="entries/", blank=True, null=True)
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
