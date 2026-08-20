from rest_framework import serializers


class CardPairSerializer(serializers.Serializer):
    """Пара, по которой карточка узнаётся в колоде."""

    arabic = serializers.CharField()
    translation_ru = serializers.CharField()


class KnownSerializer(serializers.Serializer):
    """О чём спрашивает бот: пары из разобранной вставки."""

    cards = serializers.ListField(child=CardPairSerializer(), allow_empty=False)
