from rest_framework import serializers

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
