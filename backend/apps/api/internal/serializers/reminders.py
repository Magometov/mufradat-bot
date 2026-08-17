from rest_framework import serializers


class ReminderSerializer(serializers.Serializer):
    """Карточка для чата: кому и что отправить."""

    telegram_id = serializers.IntegerField(source="learner.telegram_id")
    arabic = serializers.CharField(source="card.arabic")
    translation_ru = serializers.CharField(source="card.translation_ru")
    transliteration = serializers.CharField(source="card.transliteration")
    # Путь, а не полный адрес: он собрался бы от внутреннего хоста, а такую ссылку
    # Telegram не скачает. Публичный адрес подставляет бот — он его знает.
    image = serializers.ImageField(source="card.image")
    # Первое сообщение человеку идёт со вступлением.
    is_first = serializers.BooleanField()
