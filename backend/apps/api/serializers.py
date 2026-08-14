from rest_framework import serializers


class CardSerializer(serializers.Serializer):
    """Карточка колоды: форма слова и фраза едут в приложение одинаково."""

    id = serializers.CharField()
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField()
    is_word = serializers.BooleanField()
    image = serializers.CharField(allow_null=True)
    themes = serializers.ListField(child=serializers.CharField())


class ThemeSerializer(serializers.Serializer):
    """Сериализатор для тем."""

    slug = serializers.CharField()
    name = serializers.CharField()
