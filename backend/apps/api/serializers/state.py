from rest_framework import serializers

from apps.learning.models import CardState
from apps.vocabulary.utils import to_id


class CardStateSerializer(serializers.Serializer):
    """Что человек помнит про карточку."""

    id = serializers.SerializerMethodField()
    level = serializers.IntegerField()
    step = serializers.IntegerField()
    # Ступень падения: по ней приложение предсказывает срок переученной карточки.
    lapsed_from = serializers.IntegerField()
    due_at = serializers.DateTimeField()

    def get_id(self, state: CardState) -> str:
        return to_id(state.form_id or state.phrase_id, is_word=state.form_id is not None)


class StateSerializer(serializers.Serializer):
    """Прогресс человека и правила расписания: по ним приложение собирает сеанс."""

    enabled = serializers.BooleanField()
    # Время сервера: сроки нельзя считать по часам телефона, они врут.
    now = serializers.DateTimeField()
    ladder = serializers.ListField(child=serializers.IntegerField())
    jitter = serializers.IntegerField()
    session_limit = serializers.IntegerField()
    new_limit = serializers.IntegerField()
    first_sight_level = serializers.IntegerField()
    needed = serializers.IntegerField()
    lapse_drop = serializers.IntegerField()
    # Сколько оценок принимает ручка за раз: приложение по этому числу нарезает очередь.
    answers_limit = serializers.IntegerField()
    cards = CardStateSerializer(many=True)
