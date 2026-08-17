"""Сериализаторы служебных ручек: по файлу на дело."""

from apps.api.internal.serializers.cards import FormSerializer, PhraseSerializer
from apps.api.internal.serializers.group import GroupCardSerializer, GroupTakeSerializer
from apps.api.internal.serializers.lesson import MoveSerializer
from apps.api.internal.serializers.progress import LearnerSerializer, ProgressSerializer
from apps.api.internal.serializers.reminders import ReminderSerializer

__all__ = [
    "FormSerializer",
    "GroupCardSerializer",
    "GroupTakeSerializer",
    "LearnerSerializer",
    "MoveSerializer",
    "PhraseSerializer",
    "ProgressSerializer",
    "ReminderSerializer",
]
