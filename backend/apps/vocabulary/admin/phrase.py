"""Админка фразы: форм у неё нет, поэтому текст правится на месте."""

from django.contrib import admin

from apps.vocabulary.admin.base import CardAdmin
from apps.vocabulary.admin.filters import ThemeFilter
from apps.vocabulary.models import Phrase


@admin.register(Phrase)
class PhraseAdmin(CardAdmin):
    list_display = ("translation_ru", "theme_names", "created_at")
    list_filter = (ThemeFilter,)
    search_fields = ("translation_ru", "transliteration")
