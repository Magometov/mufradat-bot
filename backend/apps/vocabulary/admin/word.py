"""Админка слова: сверху темы, ниже формы числом."""

from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextInputWidget
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from apps.vocabulary.admin.base import CardAdmin
from apps.vocabulary.admin.filters import ThemeFilter
from apps.vocabulary.constants import Number
from apps.vocabulary.models import Word, WordForm


class WordFormInline(admin.StackedInline):
    """Написания слова: единственное и множественное число."""

    model = WordForm
    extra = 0
    max_num = len(Number.choices)
    # Превью перед картинкой, а не рядом: поле файла админка рисует внутри fieldset,
    # и в одной строке он распирает ряд.
    fields = (
        "number",
        "arabic",
        ("translation_ru", "transliteration"),
        "preview",
        "image",
    )
    readonly_fields = ("preview",)
    # Слово в строку не помещать: TextField иначе рисуется полем в десять строк.
    formfield_overrides = {models.TextField: {"widget": AdminTextInputWidget}}

    class Media:
        css = {"all": ("vocabulary/admin/word-form.css",)}

    def formfield_for_dbfield(
        self,
        db_field: models.Field,
        request: HttpRequest | None,
        **kwargs: Any,
    ) -> forms.Field | None:
        """Арабскому — свой класс: направление и размер заданы в CSS инлайна."""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)

        if field and db_field.name == "arabic":
            attrs = field.widget.attrs
            attrs["class"] = f"{attrs.get('class', '')} WordFormArabic".strip()

        return field

    @admin.display(description="Превью")
    def preview(self, obj: WordForm) -> str:
        """Миниатюра к форме."""
        if not obj.image:
            return "—"

        return format_html('<img src="{}" class="WordFormPreview" alt="">', obj.image.url)


@admin.register(Word)
class WordAdmin(CardAdmin):
    inlines = (WordFormInline,)
    list_display = ("title", "form_names", "theme_names", "created_at")
    list_filter = (ThemeFilter,)
    search_fields = ("forms__translation_ru", "forms__transliteration")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Word]:
        return super().get_queryset(request).prefetch_related("forms")

    @admin.display(description="Слово")
    def title(self, obj: Word) -> str:
        return str(obj)

    @admin.display(description="Формы")
    def form_names(self, obj: Word) -> str:
        labels = dict(Number.choices)

        return ", ".join(labels[form.number] for form in obj.forms.all()) or "—"
