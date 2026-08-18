from django.conf import settings
from rest_framework import serializers

from apps.learning.constants import Verdict
from apps.vocabulary.utils import PHRASE, WORD


class AnswerSerializer(serializers.Serializer):
    """Одна оценка: номер карточки и что человек про неё сказал."""

    card_id = serializers.RegexField(rf"^[{WORD}{PHRASE}]\d+$")
    verdict = serializers.ChoiceField(choices=Verdict.choices)
    # Когда нажали: срок считается от него, а не от того, когда доехала пачка.
    answered_at = serializers.DateTimeField()


class AnswerListSerializer(serializers.Serializer):
    """Пачка оценок: приложение копит их и отправляет разом."""

    answers = serializers.ListField(
        child=AnswerSerializer(),
        allow_empty=False,
        max_length=settings.ANSWERS_LIMIT,
    )
