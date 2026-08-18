from django.apps import AppConfig


class VocabularyConfig(AppConfig):
    name = "apps.vocabulary"
    verbose_name = "Словарный запас"

    def ready(self) -> None:
        """Подписки на сохранение карточки. Импорт здесь — модели уже готовы."""
        from apps.vocabulary import signals  # noqa: F401
