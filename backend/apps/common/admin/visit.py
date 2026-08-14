"""Журнал входов в админке: только смотреть."""

from django.contrib import admin
from django.http import HttpRequest

from apps.common.models import Visit
from apps.common.utils.devices import device_name


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("created_at", "source", "telegram_id", "username", "device")
    list_filter = ("source", "created_at")
    # `__exact` вместо простого поля: по числовой колонке искать подстрокой postgres не умеет.
    search_fields = ("username", "telegram_id__exact")
    date_hierarchy = "created_at"

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Записи заводит приложение, руками их не добавляют."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Visit | None = None) -> bool:
        """Журнал не правят: правленому журналу нет веры."""
        return False

    @admin.display(description="Устройство")
    def device(self, obj: Visit) -> str:
        return device_name(obj.user_agent) or "—"
