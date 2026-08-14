"""Регистрация в админке. Импорт нужен сам по себе: `@admin.register` срабатывает
при загрузке модуля, а Django загружает только `admin` приложения."""

from apps.vocabulary.admin.phrase import PhraseAdmin
from apps.vocabulary.admin.word import WordAdmin

__all__ = ["PhraseAdmin", "WordAdmin"]
