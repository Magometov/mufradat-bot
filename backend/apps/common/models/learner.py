from django.db import models

from apps.common.constants import KEY_HASH_LENGTH, USERNAME_LENGTH


class Learner(models.Model):
    """Человек, который учит колоду. Строка на человека, а не на заход."""

    telegram_id = models.BigIntegerField("Telegram id", null=True, blank=True, unique=True)
    key_hash = models.CharField(
        "Хэш ключа",
        max_length=KEY_HASH_LENGTH,
        null=True,
        blank=True,
        unique=True,
    )
    username = models.CharField("Ник", max_length=USERNAME_LENGTH, blank=True, default="")
    scheduling = models.BooleanField("Новая логика", default=False)
    reminders_on = models.BooleanField("Напоминания", default=True)
    created_at = models.DateTimeField("Первый заход", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Человек"
        verbose_name_plural = "Люди"
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(telegram_id__isnull=False) | models.Q(key_hash__isnull=False),
                name="learner_has_identity",
            ),
        ]

    def __str__(self) -> str:
        if self.username:
            return f"@{self.username}"

        return str(self.telegram_id) if self.telegram_id else f"гость №{self.pk}"
