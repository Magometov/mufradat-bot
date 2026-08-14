from django.db import models


class Card(models.Model):
    """Общее у формы слова и фразы: что написано на карточке и картинка к этому."""

    arabic = models.TextField("Арабское", help_text="С огласовками")
    translation_ru = models.TextField("Перевод")
    transliteration = models.TextField("Транслитерация", blank=True, default="")
    image = models.ImageField("Картинка", upload_to="entries/", blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.arabic} — {self.translation_ru}"
