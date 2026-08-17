from rest_framework import serializers


class LearnerSerializer(serializers.Serializer):
    """Кого спрашивает бот: id из апдейта Telegram, подписи там нет."""

    telegram_id = serializers.IntegerField(min_value=1)
    username = serializers.CharField(required=False, allow_blank=True, default="")


class ProgressSerializer(serializers.Serializer):
    """Сводка по человеку для команд бота."""

    reminders_on = serializers.BooleanField()
    scheduling = serializers.BooleanField()
    cards = serializers.IntegerField()
