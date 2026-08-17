"""Состояния карточек в админке: только смотреть."""

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.learning.models import CardState


@admin.register(CardState)
class CardStateAdmin(admin.ModelAdmin):
    list_display = ("learner", "card", "level", "step", "due_at", "reminded_at")
    list_filter = ("level", "due_at")
    search_fields = ("learner__username", "form__arabic", "phrase__arabic")
    date_hierarchy = "due_at"

    def get_queryset(self, request: HttpRequest) -> QuerySet[CardState]:
        """Человек и карточка нужны в каждой строке списка."""
        return super().get_queryset(request).select_related("learner", "form", "phrase")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Состояния пишет приложение."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: CardState | None = None) -> bool:
        """Уровни правит только оценка, иначе расписание разъедется."""
        return False

    @admin.display(description="Карточка")
    def card(self, obj: CardState) -> str:
        return str(obj.card)
