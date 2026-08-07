from django.db import models


class Theme(models.TextChoices):
    """Темы колоды."""

    NUMBERS = "numbers", "Цифры"
    FAMILY = "family", "Семья"
    GREETINGS = "greetings", "Знакомство"
    VERBS = "verbs", "Глаголы"
    ANTONYMS = "antonyms", "Антонимы"
    NOUNS = "nouns", "Существительные"
    QUESTIONS = "questions", "Вопросы и предлоги"
