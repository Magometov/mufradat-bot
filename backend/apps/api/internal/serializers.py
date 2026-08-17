from rest_framework import serializers

from apps.vocabulary import services
from apps.vocabulary.constants import Number
from apps.vocabulary.models import Word


class FormSerializer(serializers.Serializer):
    """Форма слова из бота. Без `word` слово создаётся новым."""

    word = serializers.PrimaryKeyRelatedField(
        queryset=Word.objects.all(), required=False, allow_null=True
    )
    number = serializers.ChoiceField(choices=Number.choices)
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField(required=False, allow_blank=True, default="")
    image = serializers.ImageField(required=False, allow_null=True)


class PhraseSerializer(serializers.Serializer):
    """Фраза из бота: чисел у неё не бывает, поэтому нет и слова-владельца."""

    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField(required=False, allow_blank=True, default="")
    image = serializers.ImageField(required=False, allow_null=True)


class MoveSerializer(serializers.Serializer):
    """Куда вынести единицу из раздела урока. Пустой список — оставить без тем."""

    kind = serializers.ChoiceField(choices=tuple(services.UNITS))
    id = serializers.IntegerField(min_value=1)
    # Выбор ограничен целями разбора, поэтому сам раздел урока отсеется здесь же.
    themes = serializers.ListField(child=serializers.ChoiceField(choices=services.move_targets()))


class ReminderSerializer(serializers.Serializer):
    """Карточка для чата: кому и что отправить."""

    telegram_id = serializers.IntegerField(source="learner.telegram_id")
    arabic = serializers.CharField(source="card.arabic")
    translation_ru = serializers.CharField(source="card.translation_ru")
    transliteration = serializers.CharField(source="card.transliteration")
    image = serializers.ImageField(source="card.image")
    # Первое сообщение человеку идёт со вступлением.
    is_first = serializers.BooleanField()
