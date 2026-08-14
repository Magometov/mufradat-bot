"""Фильтры в правой колонке списка."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.vocabulary.constants import Theme


class ThemeFilter(admin.SimpleListFilter):
    """Фильтр по теме, плюс отдельный пункт для карточек без тем."""

    title = "Тема"
    parameter_name = "theme"
    NONE = "none"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [*Theme.choices, (self.NONE, "Без темы")]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value is None:
            return queryset
        if value == self.NONE:
            return queryset.filter(themes=[])

        return queryset.filter(themes__contains=[value])
