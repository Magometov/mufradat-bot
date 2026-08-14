from django.db import models
from django.utils.timezone import localtime

from apps.common.constants import USERNAME_LENGTH, Source


class Visit(models.Model):
    """Один вход в приложение — строка на каждый заход, а не на человека."""

    source = models.CharField("Источник", max_length=16, choices=Source.choices)
    telegram_id = models.BigIntegerField("Telegram id", null=True, blank=True)
    username = models.CharField("Ник", max_length=USERNAME_LENGTH, blank=True, default="")
    user_agent = models.TextField("Браузер", blank=True, default="")
    created_at = models.DateTimeField("Когда", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Вход"
        verbose_name_plural = "Входы"
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        who = f"@{self.username}" if self.username else self.get_source_display()

        return f"{who} — {localtime(self.created_at):%d.%m.%Y %H:%M}"
