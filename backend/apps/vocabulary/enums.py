from django.db import models


class Kind(models.TextChoices):
    WORD = "word", "Слово"
    PHRASE = "phrase", "Фраза"


class Source(models.TextChoices):
    TEXTBOOK = "textbook", "Учебник"
    MANUAL = "manual", "Вручную"
    AI_GENERATED = "ai_generated", "Сгенерировано ИИ"
