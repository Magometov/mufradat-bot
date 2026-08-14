"""Регистрация в админке. Импорт нужен сам по себе: `@admin.register` срабатывает
при загрузке модуля, а Django загружает только `admin` приложения."""

from apps.common.admin.visit import VisitAdmin

__all__ = ["VisitAdmin"]
