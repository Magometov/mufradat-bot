from django.db import models

from apps.common.constants import BLANK_AND_NULL


class Card(models.Model):
    """Общее у формы слова и фразы: что написано на карточке и картинка к этому."""

    arabic = models.TextField("Арабское", help_text="С огласовками")
    translation_ru = models.TextField("Перевод")
    transliteration = models.TextField("Транслитерация", blank=True, default="")
    image = models.ImageField(
        "Картинка",
        upload_to="cards/",
        width_field="image_width",
        height_field="image_height",
        **BLANK_AND_NULL,
    )
    # Размеры едут в приложение, чтобы оно резервировало под картинку место нужной
    # формы: иначе она встаёт на место не той пропорции и при загрузке всё прыгает.
    # Заполняет их Django при сохранении файла, руками их не правят.
    image_width = models.PositiveIntegerField(editable=False, **BLANK_AND_NULL)
    image_height = models.PositiveIntegerField(editable=False, **BLANK_AND_NULL)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.arabic} — {self.translation_ru}"
