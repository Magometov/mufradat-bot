"""Админка фразы: форм у неё нет, поэтому текст правится на месте."""

from django import forms
from django.contrib import admin
from django.http import HttpRequest

from apps.vocabulary.admin.base import CardAdmin
from apps.vocabulary.admin.filters import ThemeFilter
from apps.vocabulary.models import Phrase
from apps.vocabulary.services import refresh_pictures


@admin.register(Phrase)
class PhraseAdmin(CardAdmin):
    list_display = ("translation_ru", "theme_names", "created_at")
    list_filter = (ThemeFilter,)
    search_fields = ("translation_ru", "transliteration")

    def save_model(
        self, request: HttpRequest, obj: Phrase, form: forms.ModelForm, change: bool
    ) -> None:
        """Собирает карточку для чата: на ней нарисован текст, который тут и правят."""
        super().save_model(request, obj, form, change)
        refresh_pictures(obj)
