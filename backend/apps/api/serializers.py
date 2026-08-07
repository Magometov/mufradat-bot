from rest_framework import serializers

from apps.vocabulary.models import Entry


class EntrySerializer(serializers.ModelSerializer):
    """Сериализатор для слов."""

    class Meta:
        model = Entry
        fields = ("id", "arabic", "translation_ru", "transliteration", "image", "themes")


class ThemeSerializer(serializers.Serializer):
    """Сериализатор для тем."""

    slug = serializers.CharField()
    name = serializers.CharField()
