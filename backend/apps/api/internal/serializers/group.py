from django.conf import settings
from rest_framework import serializers

from apps.api.utils import postcard_path
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
    # Собранная карточка: в группе слово должно быть видно крупно.
    image = serializers.SerializerMethodField()

    def get_chat_id(self, card: AnyCard) -> int:
        """Группа одна на всех, поэтому едет настройкой, а не полем карточки."""
        return settings.GROUP_CHAT_ID

    def get_image(self, card: AnyCard) -> str | None:
        return postcard_path(card)
