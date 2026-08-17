"""Перечисления и пределы колоды."""

from django.db import models

# Столько карточек отдаёт поиск: у инлайна в Telegram потолок тот же.
SEARCH_LIMIT = 50


class Number(models.IntegerChoices):
    """Число формы. Значения растут по величине, чтобы формы сортировались сами."""

    SINGULAR = 1, "Единственное"
    PLURAL = 2, "Множественное"


class Theme(models.TextChoices):
    """Разделы колоды: по ним собраны кнопки на главной, порядок здесь — порядок кнопок."""

    LAST_LESSON = "last_lesson", "Новое в колоде"
    NUMBERS = "numbers", "Цифры"
    FAMILY = "family", "Семья"
    GREETINGS = "greetings", "Знакомство"
    VERBS = "verbs", "Глаголы"
    ANTONYMS = "antonyms", "Антонимы"
    NOUNS = "nouns", "Существительные"
    QUESTIONS = "questions", "Вопросы и предлоги"
