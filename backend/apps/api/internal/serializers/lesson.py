from rest_framework import serializers

from apps.vocabulary.services import UNITS, move_targets


class MoveSerializer(serializers.Serializer):
    """Куда вынести единицу из раздела урока. Пустой список — оставить без тем."""

    kind = serializers.ChoiceField(choices=tuple(UNITS))
    id = serializers.IntegerField(min_value=1)
    # Выбор ограничен целями разбора, поэтому сам раздел урока отсеется здесь же.
    themes = serializers.ListField(child=serializers.ChoiceField(choices=move_targets()))
