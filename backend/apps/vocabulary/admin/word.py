"""Админка слова: сверху темы, ниже формы числом."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.vocabulary.admin.base import CardAdmin
from apps.vocabulary.admin.filters import ThemeFilter
from apps.vocabulary.constants import Number
from apps.vocabulary.models import Word, WordForm


class WordFormInline(admin.TabularInline):
    """Написания слова: единственное и множественное число."""

    model = WordForm
    extra = 0
    max_num = len(Number.choices)
    fields = ("number", "arabic", "translation_ru", "transliteration", "image")


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
