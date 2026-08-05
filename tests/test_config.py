from pathlib import Path

import pytest
from pydantic import ValidationError

from mufradat.config import Settings

ENV_VARS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "BOT_TOKEN",
    "ADMIN_TELEGRAM_IDS",
    "ANTHROPIC_API_KEY",
    "AI_MODEL",
    "WEBAPP_URL",
)

# Minimum needed to construct Settings, since these fields have no defaults.
REQUIRED = {
    "postgres_user": "u",
    "postgres_password": "p",
    "postgres_db": "d",
    "postgres_host": "h",
    "postgres_port": 5433,
    "django_secret_key": "k",
}

DOTENV_REQUIRED = """
POSTGRES_USER=u
POSTGRES_PASSWORD=p
POSTGRES_DB=d
POSTGRES_HOST=h
POSTGRES_PORT=5433
DJANGO_SECRET_KEY=k
"""


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Изолировать тесты от того, что разработчик держит в окружении."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def write_dotenv(tmp_path: Path, body: str) -> Path:
    path = tmp_path / ".env"
    path.write_text(body, encoding="utf-8")
    return path


def test_database_fields_are_required() -> None:
    # No defaults on purpose: a missing variable must name itself, not silently
    # point the app at some other database.
    with pytest.raises(ValidationError, match="postgres_user"):
        Settings(_env_file=None)


def test_secret_key_is_required() -> None:
    without_key = {key: value for key, value in REQUIRED.items() if key != "django_secret_key"}

    with pytest.raises(ValidationError, match="django_secret_key"):
        Settings(**without_key, _env_file=None)


def test_blank_value_is_treated_as_missing() -> None:
    # A .env copied from the template holds VAR= everywhere; that must read as
    # "not filled in", not as an empty username.
    incomplete = REQUIRED | {"postgres_user": "   "}

    with pytest.raises(ValidationError, match="postgres_user"):
        Settings(**incomplete, _env_file=None)


def test_reads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "env_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "env_pw")
    monkeypatch.setenv("POSTGRES_DB", "env_db")
    monkeypatch.setenv("POSTGRES_HOST", "env_host")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "env_key")

    settings = Settings(_env_file=None)

    assert settings.postgres_user == "env_user"
    assert settings.postgres_db == "env_db"
    assert settings.postgres_host == "env_host"
    assert settings.postgres_port == 6543
    assert settings.postgres_password.get_secret_value() == "env_pw"


def test_reads_values_from_dotenv_file(tmp_path: Path) -> None:
    settings = Settings(_env_file=write_dotenv(tmp_path, DOTENV_REQUIRED))

    assert settings.postgres_user == "u"
    assert settings.postgres_port == 5433


def test_admin_ids_from_dotenv_file(tmp_path: Path) -> None:
    # Regression: a complex type read through the dotenv source used to be
    # JSON-decoded before any validator ran, so "111,222" raised SettingsError.
    dotenv = write_dotenv(tmp_path, DOTENV_REQUIRED + "ADMIN_TELEGRAM_IDS=111,222\n")

    settings = Settings(_env_file=dotenv)

    assert settings.admin_telegram_ids == [111, 222]


def test_blank_admin_ids_in_dotenv_file_gives_empty_list(tmp_path: Path) -> None:
    # Same regression, blank case: the template ships ADMIN_TELEGRAM_IDS= empty.
    dotenv = write_dotenv(tmp_path, DOTENV_REQUIRED + "ADMIN_TELEGRAM_IDS=\n")

    settings = Settings(_env_file=dotenv)

    assert settings.admin_telegram_ids == []


def test_admin_ids_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", " 111 , 222 , ")

    settings = Settings(**REQUIRED, _env_file=None)

    assert settings.admin_telegram_ids == [111, 222]


def test_admin_ids_absent_gives_empty_list() -> None:
    assert Settings(**REQUIRED, _env_file=None).admin_telegram_ids == []


def test_is_admin() -> None:
    settings = Settings(**REQUIRED, admin_telegram_ids="111", _env_file=None)

    assert settings.is_admin(111) is True
    assert settings.is_admin(222) is False


def test_ai_model_has_default() -> None:
    # Operational default kept in code so the whole group moves together.
    assert Settings(**REQUIRED, _env_file=None).ai_model == "claude-sonnet-5"


def test_django_debug_is_off_unless_enabled() -> None:
    assert Settings(**REQUIRED, _env_file=None).django_debug is False
    assert Settings(**REQUIRED, django_debug="true", _env_file=None).django_debug is True


def test_optional_fields_default_to_none() -> None:
    settings = Settings(**REQUIRED, _env_file=None)

    assert settings.bot_token is None
    assert settings.anthropic_api_key is None
    assert settings.webapp_url is None


def test_secrets_are_hidden_in_repr() -> None:
    # Distinctive values, not the word "secret": that substring also occurs in the
    # field name django_secret_key, so asserting on it would test nothing.
    settings = Settings(
        **REQUIRED | {"postgres_password": "pw-xyz", "django_secret_key": "key-qaz"},
        bot_token="123:tok-abc",
        _env_file=None,
    )

    dumped = repr(settings)
    assert "pw-xyz" not in dumped
    assert "key-qaz" not in dumped
    assert "tok-abc" not in dumped
    assert settings.bot_token is not None
    assert settings.bot_token.get_secret_value() == "123:tok-abc"
