"""Общее у админки слова и фразы."""

from django import forms
from django.contrib import admin
from django.core.files.base import File
from django.core.files.uploadedfile import UploadedFile

from apps.vocabulary.constants import Theme
from apps.vocabulary.models import Phrase, Word
from apps.vocabulary.utils import to_webp


class ImageForm(forms.ModelForm):
    """Ручная загрузка ложится в колоду тем же webp, что и картинки от бота."""

    def clean_image(self) -> File | None:
        image = self.cleaned_data.get("image")

        # Файл не меняли: в поле лежит уже сохранённый, пережимать его заново нечего.
        if not isinstance(image, UploadedFile):
            return image

        return to_webp(image)


class ThemesForm(ImageForm):
    """Темы — чекбоксы: по умолчанию массив правился бы строкой через запятую.

    Модель не названа: форма одна на слово и на фразу, подставляет её админка.
    """

    themes = forms.MultipleChoiceField(
        label="Темы",
        choices=Theme.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class CardAdmin(admin.ModelAdmin):
    """Слово и фраза правятся одинаково: те же темы, та же дата только на чтение."""

    form = ThemesForm
    readonly_fields = ("created_at",)

    @admin.display(description="Темы")
    def theme_names(self, obj: Word | Phrase) -> str:
        labels = dict(Theme.choices)

        return ", ".join(labels.get(slug, slug) for slug in obj.themes) or "—"
