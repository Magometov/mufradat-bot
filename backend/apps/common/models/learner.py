from django.db import models

from apps.common.constants import BLANK_AND_NULL, KEY_HASH_LENGTH, USERNAME_LENGTH
from apps.common.models.base import BaseModel


class Learner(BaseModel):
    """Человек, который учит колоду: строка на человека, а не на заход."""

    telegram_id = models.BigIntegerField("Telegram id", unique=True, **BLANK_AND_NULL)
    # Хранится хэш, а не сам ключ гостя.
    key_hash = models.CharField(
        "Хэш ключа",
        max_length=KEY_HASH_LENGTH,
        unique=True,
        **BLANK_AND_NULL,
    )
    username = models.CharField("Ник", max_length=USERNAME_LENGTH, blank=True, default="")
    scheduling = models.BooleanField("Новая логика", default=False)
    reminders_on = models.BooleanField("Напоминания", default=True)

    class Meta(BaseModel.Meta):
        verbose_name = "Человек"
        verbose_name_plural = "Люди"
        constraints = [
            # Без способа опознания запись не найти, а прогресс к ней уже привязан.
            models.CheckConstraint(
                condition=models.Q(telegram_id__isnull=False) | models.Q(key_hash__isnull=False),
                name="learner_has_identity",
            ),
        ]

    def __str__(self) -> str:
        if self.username:
            return f"@{self.username}"

        return str(self.telegram_id) if self.telegram_id else f"гость №{self.pk}"
