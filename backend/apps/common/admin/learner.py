"""Люди в админке."""

from django.contrib import admin
from django.http import HttpRequest

from apps.common.models import Learner


@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ("created_at", "who", "scheduling", "reminders_on")
    list_editable = ("scheduling",)
    list_filter = ("scheduling", "reminders_on", "created_at")
    # `__exact` вместо простого поля: по числовой колонке искать подстрокой postgres не умеет.
    search_fields = ("username", "telegram_id__exact")
    date_hierarchy = "created_at"

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Записи заводит приложение при первом заходе."""
        return False

    @admin.display(description="Кто", ordering="username")
    def who(self, obj: Learner) -> str:
        return str(obj)
