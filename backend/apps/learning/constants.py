"""Уровни, оценки и напоминания."""

from datetime import timedelta

from django.db import models

# Срок «сейчас»: карточка попадает в каждый сеанс, пока не выучится.
LEARNING = 0
# Первая ступень расписания — на неё уходит закрытое изучение.
FIRST_SCHEDULED = 1
# Столько верных ответов подряд закрывает изучение.
NEEDED = 2

# Напоминания в чат: шаг между сообщениями и окно, вне которого бот молчит.
REMINDER_STEP = timedelta(hours=1)
AWAKE_FROM = 9
AWAKE_TO = 21


class Verdict(models.TextChoices):
    """Что человек сказал про карточку."""

    KNOW = "know", "Помню"
    FORGOT = "forgot", "Не помню"
