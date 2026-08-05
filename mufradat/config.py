from functools import lru_cache
from typing import Annotated

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из переменных окружения (и `.env`), общие для веба и бота.

    Данные живут в окружении, а не здесь: у параметров БД и секретного ключа нет
    значений по умолчанию, поэтому отсутствующая переменная роняет запуск с именем
    поля, а не приводит к тихому подключению не туда.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Read by docker-compose.yml from the same variables, so credentials exist in
    # exactly one place: .env.
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str
    postgres_port: int

    django_secret_key: SecretStr
    # A switch, not data: off unless the environment turns it on.
    django_debug: bool = False

    bot_token: SecretStr | None = None
    # NoDecode stops pydantic-settings from JSON-decoding the raw value: for a
    # complex type it would try that before any validator runs, and choke on the
    # comma-separated form a .env file can actually hold.
    admin_telegram_ids: Annotated[list[int], NoDecode] = []

    anthropic_api_key: SecretStr | None = None
    # Operational default, deliberately in code so the whole group moves together.
    ai_model: str = "claude-sonnet-5"

    webapp_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _ignore_blank_values(cls, data: object) -> object:
        """Считать `VAR=` отсутствующим значением.

        В `.env`, скопированном из `.env.example`, пусто у каждого ключа. Отбрасывая
        пустые значения, получаем внятную ошибку «поле обязательно» вместо пустого
        логина, доехавшего до драйвера базы.
        """
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
        """Принять список через запятую: JSON-список в `.env` держать неудобно."""
        if isinstance(value, str):
            return [int(part) for part in value.split(",") if part.strip()]
        return value

    def is_admin(self, telegram_id: int) -> bool:
        """Единственное место, где решается вопрос о правах админа."""
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    """Вернуть настройки, прочитав окружение один раз за процесс."""
    return Settings()
