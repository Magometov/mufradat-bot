from django.db import models


class Kind(models.TextChoices):
    WORD = "word", "Слово"
    PHRASE = "phrase", "Фраза"
