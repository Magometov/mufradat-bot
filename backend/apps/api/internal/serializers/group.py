from django.conf import settings
from rest_framework import serializers

from apps.learning.queryset import AnyCard


class GroupTakeSerializer(serializers.Serializer):
    """Просьба бота: `forced` — прислать слово сейчас, не дожидаясь часа."""

    forced = serializers.BooleanField(required=False, default=False)


class GroupCardSerializer(serializers.Serializer):
    """Слово для группы: куда слать и что показать. Спойлера нет, карточка открыта."""

    chat_id = serializers.SerializerMethodField()
    arabic = serializers.CharField()
    translation_ru = serializers.CharField()
    transliteration = serializers.CharField()
    # Путь, а не полный адрес: он собрался бы от внутреннего хоста, а такую ссылку
    # Telegram не скачает. Публичный адрес подставляет бот — он его знает.
    image = serializers.ImageField()

    def get_chat_id(self, card: AnyCard) -> int:
        """Группа одна на всех, поэтому едет настройкой, а не полем карточки."""
        return settings.GROUP_CHAT_ID
