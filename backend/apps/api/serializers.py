from rest_framework import serializers

from apps.vocabulary.models import Entry


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ("id", "arabic", "translation_ru", "transliteration", "image")
