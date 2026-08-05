from functools import lru_cache
from typing import Annotated

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из окружения и `.env`; общие для веба и бота."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Без значений по умолчанию: те же переменные читает docker-compose, поэтому
    # данные живут только в .env, а пропущенная переменная роняет старт с именем поля.
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str
    postgres_port: int

    django_secret_key: SecretStr
    django_debug: bool = False

    bot_token: SecretStr | None = None
    # NoDecode отключает JSON-разбор значения: для составного типа он идёт до любых
    # валидаторов и падает на записи через запятую, которую только и держит .env.
    admin_telegram_ids: Annotated[list[int], NoDecode] = []

    anthropic_api_key: SecretStr | None = None
    # Дефолт в коде намеренно: модель меняется для всей группы сразу.
    ai_model: str = "claude-sonnet-5"

    webapp_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _ignore_blank_values(cls, data: object) -> object:
        """Считать `VAR=` отсутствующим, чтобы шаблонный `.env` давал понятную ошибку."""
        if isinstance(data, dict):
            return {
                key: value
                for key, value in data.items()
                if not (isinstance(value, str) and not value.strip())
            }
        return data

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        """Разобрать список ID, записанный через запятую."""
        if isinstance(value, str):
            return [int(part) for part in value.split(",") if part.strip()]
        return value

    def is_admin(self, telegram_id: int) -> bool:
        """Единственное место, где решается вопрос о правах админа."""
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    """Прочитать окружение один раз за процесс."""
    return Settings()
