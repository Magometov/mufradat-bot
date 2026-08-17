"""Люди в админке: смотреть и включать новую логику."""

from django.contrib import admin
from django.http import HttpRequest

from apps.common.models import Learner


@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ("created_at", "who", "scheduling", "reminders_on")
    list_editable = ("scheduling",)
    list_filter = ("scheduling", "reminders_on", "created_at")
    search_fields = ("username", "telegram_id__exact")
    date_hierarchy = "created_at"

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Записи заводит приложение при первом заходе, руками их не добавляют."""
        return False

    @admin.display(description="Кто", ordering="username")
    def who(self, obj: Learner) -> str:
        return str(obj)
