from django.db import models


class TelegramUser(models.Model):
    """Участник группы. Запись заводит бот при первом `/start`.

    Отдельно от auth-пользователя Django: у ученика нет пароля, а у staff нет
    Telegram ID.
    """

    telegram_id = models.BigIntegerField("Telegram ID", primary_key=True)
    username = models.TextField("Ник", blank=True, default="")
    first_name = models.TextField("Имя", blank=True, default="")
    is_admin = models.BooleanField("Админ", default=False, help_text="Может наполнять колоду")
    created_at = models.DateTimeField("Первый вход", auto_now_add=True)

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self) -> str:
        return self.username or self.first_name or str(self.telegram_id)
