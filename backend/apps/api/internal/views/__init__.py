"""Виды служебных ручек: по файлу на дело."""

from apps.api.internal.views.cards import FormCreateView, PhraseCreateView
from apps.api.internal.views.group import GroupCardView
from apps.api.internal.views.lesson import LessonMoveView, LessonView
from apps.api.internal.views.progress import ProgressResetView, ProgressView
from apps.api.internal.views.reminders import RemindersSwitchView, ReminderTakeView
from apps.api.internal.views.search import SearchView

__all__ = [
    "FormCreateView",
    "GroupCardView",
    "LessonMoveView",
    "LessonView",
    "PhraseCreateView",
    "ProgressResetView",
    "ProgressView",
    "ReminderTakeView",
    "RemindersSwitchView",
    "SearchView",
]
