# Mufradat Bot — план 1: каркас и домен (Django)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Поднять Django-проект с рабочей БД, схемой данных, админкой, протестированной логикой обработки арабского и редактируемым файлом поведения ИИ — фундамент, на который встанут бот, API и Mini App.

**Architecture:** Проект Django `mufradat/` (настройки, конфиг) плюс приложение `vocabulary/` (модели, админка, домен). Настройки читаются один раз через `pydantic-settings`, `settings.py` собирает из них `DATABASES` — параметры БД не дублируются между `docker-compose.yml` и приложением. Логика обработки арабского живёт в `vocabulary/services/arabic.py` как чистые функции без БД и тестируется полностью; всё, что требует БД, тестируется на реальном Postgres 16 через `pytest-django`, который сам создаёт и удаляет тестовую базу.

**Tech Stack:** Python 3.12, Django 6.0, psycopg 3.3, Postgres 16 в Docker, pydantic-settings, PyYAML, Pillow, pytest + pytest-django, uv.

Покрывает этапы 1–2 спеки `docs/superpowers/specs/2026-08-05-mufradat-bot-design.md` (ревизия 3).

## Global Constraints

- Python 3.12 (`requires-python = ">=3.12,<3.13"`). Зависимости — через `uv sync`.
- Идентификаторы и построчные комментарии — на английском, **docstring — на
  русском** (решение владельца по ходу задачи 1). Всё, что видит пользователь
  (админка, данные сидера) — на русском.
- Локальный Postgres 14 не трогаем: контейнер слушает **порт 5433**.
- Никаких секретов в коде. `.env` в `.gitignore`; `.env.example` — только имена и
  комментарии, без значений.
- Версии (проверены на PyPI 2026-08-05): `django>=6.0,<6.1`,
  `psycopg[binary]>=3.3,<3.4`, `pydantic-settings>=2.14,<3`, `pillow>=12.3,<13`,
  `pyyaml>=6,<7`, `pytest>=9.1,<10`, `pytest-django>=4.12,<5`, `ruff>=0.16,<0.17`.
  DRF, aiogram, fsrs и anthropic добавляются в своих планах, не здесь.
- Django 6: у `CheckConstraint` аргумент называется `condition`, а не `check`
  (`check` удалён в 6.0).
- `USE_TZ = True`, все временные метки — `TIMESTAMPTZ`.
- Арабский в тестах и сидере — реальный, с огласовками.
- Каждая задача заканчивается коммитом, затем остановка и одобрение владельца.

---

### Task 1: Каркас Django, конфигурация, БД

**Files:**
- Modify: `pyproject.toml` (переписать под Django), `docker-compose.yml`, `.env`, `.env.example`, `.gitignore`
- Delete: `docker/init-test-db.sql`, каталог `app/` (артефакты стека SQLAlchemy)
- Create: `manage.py`, `mufradat/{__init__,settings,urls,asgi,wsgi}.py` (генерируются), `mufradat/config.py`
- Create: `vocabulary/` (генерируется `startapp`)
- Test: `tests/test_config.py` (переписать)

**Interfaces:**
- Consumes: ничего.
- Produces:
  - `mufradat.config.Settings` — **обязательные** (без значений по умолчанию, только из окружения): `postgres_user: str`, `postgres_password: SecretStr`, `postgres_db: str`, `postgres_host: str`, `postgres_port: int`, `django_secret_key: SecretStr`. Со значениями по умолчанию: `django_debug: bool = False`, `admin_telegram_ids: Annotated[list[int], NoDecode] = []`, `ai_model: str = "claude-sonnet-5"`, `bot_token`/`anthropic_api_key`/`webapp_url` = `None`. Метод `is_admin(telegram_id: int) -> bool`.
  - `mufradat.config.get_settings() -> Settings` — кэширующий геттер.
  - `mufradat.settings` — модуль настроек Django (`DJANGO_SETTINGS_MODULE`).

- [ ] **Step 1: Убрать артефакты старого стека**

Каталог `app/` и init-скрипт тестовой базы относились к SQLAlchemy. `pytest-django`
создаёт тестовую базу сам, поэтому отдельная `mufradat_test` больше не нужна.

Run: `rm -rf app docker/init-test-db.sql && docker compose exec db dropdb -U mufradat --if-exists mufradat_test && echo cleaned`
Expected: `cleaned`.

- [ ] **Step 2: Переписать `pyproject.toml`**

```toml
[project]
name = "mufradat-bot"
version = "0.1.0"
description = "Telegram Mini App for learning Arabic vocabulary with spaced repetition"
requires-python = ">=3.12,<3.13"
dependencies = [
    "django>=6.0,<6.1",
    "psycopg[binary]>=3.3,<3.4",
    "pydantic-settings>=2.14,<3",
    "pillow>=12.3,<13",
    "pyyaml>=6,<7",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.1,<10",
    "pytest-django>=4.12,<5",
    "ruff>=0.16,<0.17",
]
# Fallback diacritizer: pulls torch (~1-2 GB), so it stays out of the default set.
tashkeel = [
    "arabic-diacritizer>=1.0,<2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["mufradat", "vocabulary"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "mufradat.settings"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
# ruff format also reformats python blocks inside markdown, which mangles the
# deliberate fragments in the plans (a bare "app-name," line became a tuple).
exclude = ["docs"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.ruff.lint.per-file-ignores]
# Django migrations are generated code.
"*/migrations/*" = ["E501"]
```

- [ ] **Step 3: Убрать монтирование init-скрипта из `docker-compose.yml`**

Удалить из `volumes` сервиса `db` строку:

```yaml
      - ./docker/init-test-db.sql:/docker-entrypoint-initdb.d/init-test-db.sql:ro
```

Остальное (подстановка `${POSTGRES_*}`, порт `5433`, healthcheck) не трогать.

Run: `docker compose config --quiet && echo "compose ok"`
Expected: `compose ok`.

- [ ] **Step 4: Обновить `.env.example` и `.env`**

Из обоих файлов убрать `DATABASE_URL`: Django принимает параметры БД по частям, и
готовый DSN ему не нужен.

Добавить в `.env.example` после блока базы данных:

```
# --- Django ------------------------------------------------------------------
# Обязателен, когда DJANGO_DEBUG=false. Сгенерировать:
#   uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
```

В `.env` — те же две строки, но заполненные: `DJANGO_DEBUG=true` и настоящий ключ,
потому что `django_secret_key` обязателен:

Run: `` key=$(uv run python -c "import secrets; print(secrets.token_urlsafe(50))") && printf 'DJANGO_SECRET_KEY=%s\nDJANGO_DEBUG=true\n' "$key" ``
Expected: ключ сгенерирован и вписан в `.env` (файл в `.gitignore`).

- [ ] **Step 5: Установить зависимости**

Run: `uv sync --extra dev 2>&1 | tail -6`
Expected: среди установленного есть `django`, `psycopg`, `pytest-django`.

- [ ] **Step 6: Создать проект и приложение Django**

Run: `uv run django-admin startproject mufradat . && uv run python manage.py startapp vocabulary && ls mufradat vocabulary`
Expected: в `mufradat/` появились `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`; в `vocabulary/` — `models.py`, `admin.py`, `apps.py`, `migrations/`.

- [ ] **Step 7: Написать падающие тесты конфигурации**

Заменить содержимое `tests/test_config.py`:

```python
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
```

- [ ] **Step 8: Убедиться, что тесты падают**

Run: `uv run pytest tests/test_config.py -q 2>&1 | tail -5`
Expected: FAIL — `ModuleNotFoundError: No module named 'mufradat.config'`.

- [ ] **Step 9: Реализовать `mufradat/config.py`**

```python
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
```

- [ ] **Step 10: Убедиться, что тесты проходят**

Run: `uv run pytest tests/test_config.py -q 2>&1 | tail -3`
Expected: 14 passed.

- [ ] **Step 11: Подключить настройки к Django**

Правки в `mufradat/settings.py` точечные — сгенерированный файл не переписывать.

**11.1.** После существующих импортов добавить:

```python
from mufradat.config import get_settings

config = get_settings()
```

**11.2.** Заменить строки `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`:

```python
SECRET_KEY = config.django_secret_key.get_secret_value()
DEBUG = config.django_debug
ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
```

**11.3.** В `INSTALLED_APPS` добавить последним элементом:

```python
    "vocabulary",
```

**11.4.** Заменить блок `DATABASES` целиком:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config.postgres_db,
        "USER": config.postgres_user,
        "PASSWORD": config.postgres_password.get_secret_value(),
        "HOST": config.postgres_host,
        "PORT": str(config.postgres_port),
    }
}
```

**11.5.** Заменить локаль и часовой пояс:

```python
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
```

**11.6.** В конец файла добавить настройки медиа:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

- [ ] **Step 12: Проверить, что Django поднимается и миграции применяются**

Run: `uv run python manage.py check`
Expected: `System check identified no issues (0 silenced).`

Run: `uv run python manage.py migrate 2>&1 | tail -6`
Expected: применяются миграции `contenttypes`, `auth`, `admin`, `sessions` без ошибок.

Run: `docker compose exec db psql -U mufradat -d mufradat -c '\dt' | head -12`
Expected: в списке есть `auth_user`, `django_migrations`, `django_content_type`.

- [ ] **Step 13: Добавить `media/` в `.gitignore`, проверить линтер, закоммитить**

Дописать в `.gitignore` строку `media/`.

Run: `uv run ruff format . && uv run ruff check .`
Expected: линтер без ошибок.

```bash
git add -A
git commit -m "feat: Django project skeleton with settings sourced from one config"
```

**Проверка задачи для владельца:** `manage.py check` без замечаний, `manage.py migrate` прошёл, `uv run pytest` зелёный (14 тестов).

---

### Task 2: Нормализация арабского текста

Основа поиска похожих записей: одно и то же слово, распознанное с разной
расстановкой харакат, должно приводиться к одной форме.

**Files:**
- Create: `vocabulary/services/__init__.py`, `vocabulary/services/arabic.py`
- Test: `tests/services/__init__.py`, `tests/services/test_arabic.py`

**Interfaces:**
- Consumes: ничего (чистая логика, без БД и настроек).
- Produces: `vocabulary.services.arabic.normalize_arabic(text: str) -> str`.

- [ ] **Step 1: Написать падающие тесты**

Создать `vocabulary/services/__init__.py` и `tests/services/__init__.py` пустыми.

`tests/services/test_arabic.py`:

```python
from vocabulary.services.arabic import normalize_arabic


def test_strips_diacritics() -> None:
    assert normalize_arabic("كِتَاب") == "كتاب"


def test_strips_shadda_and_damma() -> None:
    assert normalize_arabic("مُدَرِّسٌ") == "مدرس"


def test_strips_sukun_and_tanwin() -> None:
    assert normalize_arabic("بَيْتٌ") == "بيت"


def test_unifies_alef_with_hamza() -> None:
    assert normalize_arabic("أَحْمَد") == "احمد"
    assert normalize_arabic("إِسْلَام") == "اسلام"
    assert normalize_arabic("آسِف") == "اسف"


def test_unifies_alef_maqsura_to_ya() -> None:
    assert normalize_arabic("عَلَى") == "علي"


def test_keeps_ta_marbuta_distinct_from_ha() -> None:
    # ة and ه change the meaning of a word, so they must not be merged.
    assert normalize_arabic("مَدْرَسَة") == "مدرسة"
    assert normalize_arabic("مَدْرَسَة") != normalize_arabic("مدرسه")


def test_strips_tatweel() -> None:
    assert normalize_arabic("كــتاب") == "كتاب"


def test_collapses_whitespace() -> None:
    assert normalize_arabic("  بَيْتٌ   كَبِيرٌ  ") == "بيت كبير"


def test_is_idempotent() -> None:
    once = normalize_arabic("الْمُدَرِّسُ")
    assert normalize_arabic(once) == once


def test_empty_string() -> None:
    assert normalize_arabic("") == ""


def test_non_arabic_passes_through() -> None:
    assert normalize_arabic("hello") == "hello"


def test_gender_pairs_collapse_and_that_is_expected() -> None:
    """Documents the blind spot the data model works around (spec 4.1).

    Masculine and feminine address differ only by the final harakat, which
    normalization strips. Uniqueness is therefore enforced on the exact `arabic`,
    and the pair is distinguished structurally by Entry.person.
    """
    assert normalize_arabic("مَا اسْمُكَ؟") == normalize_arabic("مَا اسْمُكِ؟")
    assert normalize_arabic("كَتَبْتَ") == normalize_arabic("كَتَبْتِ")
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_arabic.py -q 2>&1 | tail -5`
Expected: FAIL — `ModuleNotFoundError: No module named 'vocabulary.services.arabic'`.

- [ ] **Step 3: Реализовать нормализацию**

`vocabulary/services/arabic.py`:

```python
"""Pure text helpers for Arabic. No database, no settings — trivially testable."""

import re
import unicodedata

# Harakat, tanwin, shadda, sukun, superscript alef and Quranic marks.
_DIACRITICS = re.compile(r"[ً-ٰٟۖ-ۭ]")

_TATWEEL = "ـ"  # decorative letter-stretching mark, carries no meaning

# Alef variants collapse to bare alef; alef maqsura collapses to ya.
# Ta marbuta is deliberately NOT merged into ha: it changes meaning.
_LETTER_FOLDING = str.maketrans(
    {
        "أ": "ا",  # alef with hamza above -> alef
        "إ": "ا",  # alef with hamza below -> alef
        "آ": "ا",  # alef with madda above -> alef
        "ٱ": "ا",  # alef wasla -> alef
        "ى": "ي",  # alef maqsura -> ya
    }
)


def normalize_arabic(text: str) -> str:
    """Reduce an Arabic string to a lookup key for finding near-duplicates.

    Diacritics are how the textbook teaches pronunciation, so they are stored as
    recognised — but they must not participate in the lookup: the vision model may
    return the same word with slightly different harakat.

    Note the deliberate blind spot: masculine and feminine forms that differ only by
    the final harakat map to the same key. See spec 4.1 — uniqueness is enforced on
    the exact `arabic`, not on this key.
    """
    text = unicodedata.normalize("NFC", text)
    text = _DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = text.translate(_LETTER_FOLDING)
    return " ".join(text.split())
```

- [ ] **Step 4: Убедиться, что тесты проходят**

Run: `uv run pytest tests/services/test_arabic.py -q 2>&1 | tail -3`
Expected: 13 passed.

- [ ] **Step 5: Закоммитить**

```bash
git add vocabulary/services tests/services
git commit -m "feat: normalize Arabic text for near-duplicate lookup"
```

**Проверка задачи для владельца:** 13 тестов зелёные, включая тот, что фиксирует слепоту нормализации к роду.

---

### Task 3: Сопоставление слов предложения со словарём

**Files:**
- Modify: `vocabulary/services/arabic.py` (дописать в конец)
- Modify: `tests/services/test_arabic.py` (дописать в конец)

**Interfaces:**
- Consumes: `normalize_arabic`.
- Produces: `vocabulary.services.arabic.match_entries_in_sentence(sentence: str, known: dict[str, int]) -> set[int]`, где `known` — отображение `arabic_norm -> entry_id`.

- [ ] **Step 1: Написать падающие тесты**

Дописать в конец `tests/services/test_arabic.py`:

```python
from vocabulary.services.arabic import match_entries_in_sentence

# arabic_norm -> entry id
KNOWN = {
    "كتاب": 1,
    "بيت": 2,
    "قمر": 3,
    "مدرسة": 4,
    "مدرس": 5,
    "كبير": 6,
}


def test_matches_bare_word() -> None:
    assert match_entries_in_sentence("هَذَا بَيْتٌ", KNOWN) == {2}


def test_matches_word_with_definite_article() -> None:
    assert match_entries_in_sentence("الْكِتَابُ هُنَا", KNOWN) == {1}


def test_matches_word_with_conjunction_and_article() -> None:
    assert match_entries_in_sentence("وَالْقَمَرُ", KNOWN) == {3}


def test_matches_several_words_in_one_sentence() -> None:
    assert match_entries_in_sentence("الْمُدَرِّسُ فِي الْمَدْرَسَةِ", KNOWN) == {4, 5}


def test_full_form_wins_over_stripped_prefix() -> None:
    # بيت must match as a whole; it must not be read as ب + يت.
    assert match_entries_in_sentence("بَيْت", KNOWN) == {2}


def test_unknown_words_are_ignored() -> None:
    assert match_entries_in_sentence("هَذَا شَيْءٌ غَرِيبٌ", KNOWN) == set()


def test_punctuation_does_not_break_matching() -> None:
    assert match_entries_in_sentence("هَذَا بَيْتٌ كَبِيرٌ.", KNOWN) == {2, 6}


def test_empty_sentence() -> None:
    assert match_entries_in_sentence("", KNOWN) == set()


def test_empty_dictionary() -> None:
    assert match_entries_in_sentence("الْكِتَابُ", {}) == set()
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_arabic.py -q 2>&1 | tail -5`
Expected: FAIL — `ImportError: cannot import name 'match_entries_in_sentence'`.

- [ ] **Step 3: Реализовать сопоставление**

Дописать в конец `vocabulary/services/arabic.py`:

```python
_ARABIC_LETTERS = re.compile(r"[ء-ي]+")

_DEFINITE_ARTICLE = "ال"  # al-

# Single-letter proclitics that attach to the following word: wa, fa, bi, li, ka.
_PROCLITICS = ("و", "ف", "ب", "ل", "ك")


def _candidate_forms(token: str) -> list[str]:
    """Forms to try for one normalized token, most specific first.

    The full form comes first on purpose: stripping a leading letter from a word
    that simply starts with it must never win over an exact dictionary hit.
    """
    forms = [token]

    if token.startswith(_DEFINITE_ARTICLE) and len(token) > 3:
        forms.append(token[2:])

    for proclitic in _PROCLITICS:
        if token.startswith(proclitic) and len(token) > 2:
            rest = token[1:]
            forms.append(rest)
            if rest.startswith(_DEFINITE_ARTICLE) and len(rest) > 3:
                forms.append(rest[2:])

    return forms


def match_entries_in_sentence(sentence: str, known: dict[str, int]) -> set[int]:
    """Find which dictionary entries a sentence uses.

    `known` maps an entry's normalized form (Entry.arabic_norm) to its id. Needed
    because in running text a word carries the definite article and clitic
    prepositions, so a plain comparison would miss it.
    """
    if not known:
        return set()

    matched: set[int] = set()
    for token in _ARABIC_LETTERS.findall(normalize_arabic(sentence)):
        for form in _candidate_forms(token):
            entry_id = known.get(form)
            if entry_id is not None:
                matched.add(entry_id)
                break

    return matched
```

- [ ] **Step 4: Прогнать тесты файла**

Run: `uv run pytest tests/services/test_arabic.py -q 2>&1 | tail -3`
Expected: 22 passed (13 из задачи 2 + 9 новых).

- [ ] **Step 5: Закоммитить**

```bash
git add vocabulary/services/arabic.py tests/services/test_arabic.py
git commit -m "feat: match sentence tokens to dictionary entries through proclitics"
```

**Проверка задачи для владельца:** 22 теста зелёные; `وَالْقَمَرُ` находит `قمر`, а `بَيْت` не разваливается на `ب` + `يت`.

---

### Task 4: Модели данных и первая миграция

**Files:**
- Create: `vocabulary/enums.py`
- Modify: `vocabulary/models.py`
- Create: `vocabulary/migrations/0001_initial.py` (генерируется)
- Test: `tests/db/__init__.py`, `tests/db/test_models.py`

**Interfaces:**
- Consumes: `normalize_arabic`.
- Produces:
  - `vocabulary.enums`: `Kind` (`WORD`/`PHRASE`/`FORM`), `Pos` (`NOUN`/`VERB`), `Person` (`ANA`/`HUWA`/`HIYA`/`ANTA`/`ANTI`/`NAHNU`), `Tense` (`PAST`/`PRESENT`), `Direction` (`AR_RU`/`RU_AR`), `Source` (`TEXTBOOK`/`MANUAL`/`AI_GENERATED`).
  - `vocabulary.models`: `Entry` (свойства `display_image`, `display_attribution`, related_name `forms`), `TelegramUser`, `Sentence`, `SentenceEntry`, `UserProgress`, `ReviewLog`.

- [ ] **Step 1: Создать перечисления**

`vocabulary/enums.py`:

```python
from django.db import models


class Kind(models.TextChoices):
    WORD = "word", "слово"
    PHRASE = "phrase", "фраза"
    FORM = "form", "форма"


class Pos(models.TextChoices):
    """Part of speech. Only needed to decide which forms make sense."""

    NOUN = "noun", "существительное"
    VERB = "verb", "глагол"


class Person(models.TextChoices):
    ANA = "ana", "أنا (я)"
    HUWA = "huwa", "هو (он)"
    HIYA = "hiya", "هي (она)"
    ANTA = "anta", "أنتَ (ты, м)"
    ANTI = "anti", "أنتِ (ты, ж)"
    NAHNU = "nahnu", "نحن (мы)"


class Tense(models.TextChoices):
    PAST = "past", "прошедшее"
    PRESENT = "present", "настоящее"


class Direction(models.TextChoices):
    """Every entry yields two independent SRS cards."""

    AR_RU = "ar_ru", "арабское → русский"
    RU_AR = "ru_ar", "русское → арабский"


class Source(models.TextChoices):
    TEXTBOOK = "textbook", "учебник"
    MANUAL = "manual", "вручную"
    AI_GENERATED = "ai_generated", "сгенерировано ИИ"
```

- [ ] **Step 2: Написать модели**

Заменить содержимое `vocabulary/models.py`:

```python
from django.db import models
from django.db.models import Q

from vocabulary.enums import Direction, Kind, Person, Pos, Source, Tense
from vocabulary.services.arabic import normalize_arabic


class TelegramUser(models.Model):
    """A learner. Separate from Django's auth user: no password, Telegram id as pk."""

    telegram_id = models.BigIntegerField(primary_key=True)
    username = models.TextField(blank=True, default="")
    first_name = models.TextField(blank=True, default="")
    new_per_day = models.PositiveIntegerField(default=5, help_text="Лимит новых карточек в день")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ученик"
        verbose_name_plural = "ученики"

    def __str__(self) -> str:
        return self.username or str(self.telegram_id)


class Entry(models.Model):
    """A study unit: a word, a phrase or an inflected form. All three share a shape."""

    kind = models.CharField(max_length=8, choices=Kind)
    arabic = models.TextField(help_text="С огласовками, как распознано")
    # Lookup key for near-duplicates; filled in save(), see spec 4.2.
    arabic_norm = models.TextField(editable=False, db_index=True)
    translation_ru = models.TextField()
    # Service field: the Openverse image query. Never shown in the interface.
    translation_en = models.TextField(blank=True, default="")
    transliteration = models.TextField(blank=True, default="")

    pos = models.CharField(max_length=8, choices=Pos, blank=True, default="")
    base = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="forms"
    )
    person = models.CharField(max_length=8, choices=Person, blank=True, default="")
    tense = models.CharField(max_length=8, choices=Tense, blank=True, default="")

    topic = models.TextField(blank=True, default="", db_index=True)
    source = models.CharField(max_length=16, choices=Source)

    image = models.ImageField(upload_to="entries/", blank=True, null=True)
    image_attribution = models.TextField(blank=True, default="")
    image_source_url = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "единица"
        verbose_name_plural = "единицы"
        constraints = [
            # Exact arabic, NOT arabic_norm: a gender pair differs only by the final
            # harakat, and a norm-based constraint would forbid the feminine form.
            models.UniqueConstraint(
                fields=["arabic", "translation_ru"], name="uq_entry_arabic_translation"
            ),
            # One form per person and tense. person/tense are CharFields holding ""
            # rather than NULL, so a possessive form (empty tense) still compares
            # equal to another one and the constraint bites.
            models.UniqueConstraint(
                fields=["base", "person", "tense"],
                condition=Q(kind=Kind.FORM),
                name="uq_form_base_person_tense",
            ),
            models.CheckConstraint(
                condition=~Q(kind=Kind.FORM) | (Q(base__isnull=False) & ~Q(person="")),
                name="form_requires_base_and_person",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.arabic} — {self.translation_ru}"

    def save(self, *args: object, **kwargs: object) -> None:
        # Kept here so no caller can forget it. bulk_create() bypasses save() —
        # set arabic_norm explicitly there.
        self.arabic_norm = normalize_arabic(self.arabic)
        super().save(*args, **kwargs)

    @property
    def display_image(self) -> models.fields.files.ImageFieldFile | None:
        """A form shows its base's picture: "его машина" reuses the car photo."""
        if self.image:
            return self.image
        if self.base_id and self.base.image:
            return self.base.image
        return None

    @property
    def display_attribution(self) -> str:
        if self.image:
            return self.image_attribution
        return self.base.image_attribution if self.base_id else ""


class Sentence(models.Model):
    """Usage example. Never becomes a card — phrases are Entry rows instead."""

    arabic = models.TextField()
    translation_ru = models.TextField()
    source = models.CharField(max_length=16, choices=Source)
    created_at = models.DateTimeField(auto_now_add=True)
    entries = models.ManyToManyField(Entry, through="SentenceEntry", related_name="sentences")

    class Meta:
        verbose_name = "пример"
        verbose_name_plural = "примеры"

    def __str__(self) -> str:
        return self.arabic


class SentenceEntry(models.Model):
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sentence", "entry"], name="uq_sentence_entry")
        ]


class UserProgress(models.Model):
    """One row per (learner, entry, direction). FSRS runs server-side."""

    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="progress"
    )
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="progress")
    direction = models.CharField(max_length=8, choices=Direction)
    due = models.DateTimeField()
    fsrs_state = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["telegram_user", "entry", "direction"], name="uq_progress_user_entry_dir"
            )
        ]
        indexes = [models.Index(fields=["telegram_user", "due"], name="ix_progress_user_due")]


class ReviewLog(models.Model):
    """Rating history, kept to fit FSRS parameters for this group later.

    telegram_id has no FK on purpose: history outlives a deleted learner.
    """

    telegram_id = models.BigIntegerField(db_index=True)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="reviews")
    direction = models.CharField(max_length=8, choices=Direction)
    rating = models.PositiveSmallIntegerField(help_text="Шкала FSRS: 1 again … 4 easy")
    reviewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
```

- [ ] **Step 3: Сгенерировать и применить миграцию**

Run: `uv run python manage.py makemigrations vocabulary`
Expected: создан `vocabulary/migrations/0001_initial.py` с шестью моделями.

Run: `uv run python manage.py migrate`
Expected: `Applying vocabulary.0001_initial... OK`.

Run: `docker compose exec db psql -U mufradat -d mufradat -c '\dt vocabulary*'`
Expected: таблицы `vocabulary_entry`, `vocabulary_sentence`, `vocabulary_sentenceentry`, `vocabulary_telegramuser`, `vocabulary_userprogress`, `vocabulary_reviewlog`.

- [ ] **Step 4: Написать тесты моделей**

Создать `tests/db/__init__.py` пустым.

`tests/db/test_models.py`:

```python
import pytest
from django.db.utils import IntegrityError

from vocabulary.enums import Kind, Person, Source, Tense
from vocabulary.models import Entry, Sentence, SentenceEntry

pytestmark = pytest.mark.django_db


def make_word(arabic: str, translation: str) -> Entry:
    return Entry.objects.create(
        kind=Kind.WORD, arabic=arabic, translation_ru=translation, source=Source.TEXTBOOK
    )


def test_save_fills_arabic_norm() -> None:
    entry = make_word("كِتَاب", "книга")

    assert entry.arabic_norm == "كتاب"


def test_exact_duplicate_is_rejected() -> None:
    make_word("كِتَاب", "книга")

    with pytest.raises(IntegrityError):
        make_word("كِتَاب", "книга")


def test_gender_pair_is_allowed() -> None:
    """Regression test for spec 4.1.

    Both phrases normalize to the same key; uniqueness is on the exact arabic, so
    the feminine form must be storable next to the masculine one.
    """
    masculine = Entry.objects.create(
        kind=Kind.PHRASE,
        arabic="مَا اسْمُكَ؟",
        translation_ru="как тебя зовут? (к мужчине)",
        person=Person.ANTA,
        source=Source.MANUAL,
    )
    feminine = Entry.objects.create(
        kind=Kind.PHRASE,
        arabic="مَا اسْمُكِ؟",
        translation_ru="как тебя зовут? (к женщине)",
        person=Person.ANTI,
        source=Source.MANUAL,
    )

    assert masculine.arabic_norm == feminine.arabic_norm
    assert Entry.objects.filter(kind=Kind.PHRASE).count() == 2


def test_same_skeleton_with_other_translation_is_allowed() -> None:
    make_word("عَيْن", "глаз")
    make_word("عَيْن", "источник")

    assert Entry.objects.count() == 2


def test_form_requires_base_and_person() -> None:
    with pytest.raises(IntegrityError):
        Entry.objects.create(
            kind=Kind.FORM,
            arabic="سَيَّارَتُهُ",
            translation_ru="его машина",
            source=Source.MANUAL,
        )


def test_duplicate_possessive_form_is_rejected_with_empty_tense() -> None:
    # Possessive forms carry no tense; the unique constraint must still fire, which
    # is why person/tense are "" CharFields and not NULL.
    base = make_word("سَيَّارَة", "машина")
    Entry.objects.create(
        kind=Kind.FORM,
        arabic="سَيَّارَتُهُ",
        translation_ru="его машина",
        base=base,
        person=Person.HUWA,
        source=Source.MANUAL,
    )

    with pytest.raises(IntegrityError):
        Entry.objects.create(
            kind=Kind.FORM,
            arabic="سَيَّارَتُهْ",
            translation_ru="его машина (вариант)",
            base=base,
            person=Person.HUWA,
            source=Source.MANUAL,
        )


def test_same_person_different_tense_is_allowed() -> None:
    base = make_word("كَتَبَ", "писать")
    Entry.objects.create(
        kind=Kind.FORM,
        arabic="كَتَبْتُ",
        translation_ru="я написал",
        base=base,
        person=Person.ANA,
        tense=Tense.PAST,
        source=Source.MANUAL,
    )
    Entry.objects.create(
        kind=Kind.FORM,
        arabic="أَكْتُبُ",
        translation_ru="я пишу",
        base=base,
        person=Person.ANA,
        tense=Tense.PRESENT,
        source=Source.MANUAL,
    )

    assert base.forms.count() == 2


def test_form_inherits_image_from_base() -> None:
    base = make_word("سَيَّارَة", "машина")
    base.image = "entries/car.jpg"
    base.image_attribution = '"Car" by Someone, CC BY 2.0'
    base.save()
    form = Entry.objects.create(
        kind=Kind.FORM,
        arabic="سَيَّارَتُهُ",
        translation_ru="его машина",
        base=base,
        person=Person.HUWA,
        source=Source.MANUAL,
    )

    assert not form.image
    assert form.display_image is not None
    assert form.display_image.name == "entries/car.jpg"
    assert "CC BY" in form.display_attribution


def test_sentence_links_to_entry() -> None:
    entry = make_word("بَيْت", "дом")
    sentence = Sentence.objects.create(
        arabic="هَذَا بَيْتٌ كَبِيرٌ", translation_ru="Это большой дом.", source=Source.TEXTBOOK
    )
    SentenceEntry.objects.create(sentence=sentence, entry=entry)

    assert list(sentence.entries.all()) == [entry]
```

- [ ] **Step 5: Прогнать тесты**

Run: `uv run pytest -q 2>&1 | tail -3`
Expected: 45 passed (14 конфигурация + 22 арабский + 9 модели).

- [ ] **Step 6: Проверить, что модели и миграция не расходятся**

Run: `uv run python manage.py makemigrations --check --dry-run`
Expected: `No changes detected`.

- [ ] **Step 7: Закоммитить**

```bash
git add vocabulary tests
git commit -m "feat: Entry model covering words, phrases and inflected forms"
```

**Проверка задачи для владельца:** шесть таблиц в БД; пара «к мужчине / к женщине» сохраняется рядом, точный дубль отбивается, форма без базы отбивается; повторный `makemigrations` пустой.

---

### Task 5: Админка

**Files:**
- Modify: `vocabulary/admin.py`
- Test: `tests/db/test_admin.py`

**Interfaces:**
- Consumes: модели из задачи 4.
- Produces: зарегистрированные `Entry`, `Sentence`, `TelegramUser`; страницы `/admin/vocabulary/entry/`, `/admin/vocabulary/sentence/`.

- [ ] **Step 1: Написать админку**

Заменить содержимое `vocabulary/admin.py`:

```python
from django.contrib import admin

from vocabulary.models import Entry, Sentence, SentenceEntry, TelegramUser


class FormInline(admin.TabularInline):
    """Inflected forms of the entry being edited."""

    model = Entry
    fk_name = "base"
    extra = 0
    fields = ("kind", "arabic", "transliteration", "translation_ru", "person", "tense", "source")
    verbose_name = "форма"
    verbose_name_plural = "формы"


class SentenceEntryInline(admin.TabularInline):
    model = SentenceEntry
    extra = 0
    autocomplete_fields = ("entry",)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("arabic", "translation_ru", "kind", "person", "topic", "has_image")
    list_filter = ("kind", "pos", "source", "person")
    search_fields = ("arabic", "arabic_norm", "translation_ru", "translation_en")
    readonly_fields = ("arabic_norm", "created_at")
    autocomplete_fields = ("base",)
    inlines = (FormInline,)
    fieldsets = (
        (
            None,
            {"fields": ("kind", "arabic", "arabic_norm", "translation_ru", "transliteration")},
        ),
        ("Грамматика", {"fields": ("pos", "base", "person", "tense")}),
        ("Картинка", {"fields": ("image", "image_attribution", "image_source_url")}),
        ("Служебное", {"fields": ("translation_en", "topic", "source", "created_at")}),
    )

    @admin.display(boolean=True, description="картинка")
    def has_image(self, obj: Entry) -> bool:
        return bool(obj.display_image)


@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    list_display = ("arabic", "translation_ru", "source")
    list_filter = ("source",)
    search_fields = ("arabic", "translation_ru")
    inlines = (SentenceEntryInline,)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "first_name", "new_per_day", "created_at")
    search_fields = ("telegram_id", "username", "first_name")
```

- [ ] **Step 2: Написать тесты, что страницы открываются**

`tests/db/test_admin.py`:

```python
import pytest

from vocabulary.enums import Kind, Source
from vocabulary.models import Entry

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_client(client, django_user_model):
    django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="pw"
    )
    client.force_login(django_user_model.objects.get(username="admin"))
    return client


def test_entry_changelist_opens(staff_client) -> None:
    Entry.objects.create(
        kind=Kind.WORD, arabic="بَيْت", translation_ru="дом", source=Source.TEXTBOOK
    )

    response = staff_client.get("/admin/vocabulary/entry/")

    assert response.status_code == 200
    assert "дом" in response.content.decode()


def test_entry_add_form_opens(staff_client) -> None:
    assert staff_client.get("/admin/vocabulary/entry/add/").status_code == 200


def test_sentence_changelist_opens(staff_client) -> None:
    assert staff_client.get("/admin/vocabulary/sentence/").status_code == 200


def test_telegram_user_changelist_opens(staff_client) -> None:
    assert staff_client.get("/admin/vocabulary/telegramuser/").status_code == 200
```

- [ ] **Step 3: Прогнать проверку Django и тесты**

Run: `uv run python manage.py check && uv run pytest -q 2>&1 | tail -3`
Expected: проверка без замечаний, 49 passed.

- [ ] **Step 4: Создать суперпользователя для ручного захода**

Run: `uv run python manage.py createsuperuser --username admin --email admin@example.com`
Expected: пароль введён вручную, `Superuser created successfully.`

- [ ] **Step 5: Закоммитить**

```bash
git add vocabulary/admin.py tests/db/test_admin.py
git commit -m "feat: admin for entries, examples and learners"
```

**Проверка задачи для владельца:** `uv run python manage.py runserver`, открыть `http://127.0.0.1:8000/admin/` — единицы видны, фильтр по типу работает, у слова можно добавить форму инлайном.

---

### Task 6: Поиск похожих записей при импорте

**Files:**
- Create: `vocabulary/services/dedup.py`
- Test: `tests/services/test_dedup.py`

**Interfaces:**
- Consumes: `Entry`, `normalize_arabic`.
- Produces:
  - `vocabulary.services.dedup.DuplicateKind` — `NONE`, `EXACT`, `SIMILAR`.
  - `vocabulary.services.dedup.DuplicateCheck` — frozen dataclass: `kind`, `existing_id: int | None`, `existing_arabic: str | None`, `existing_translation: str | None`, `same_translation: bool`.
  - `vocabulary.services.dedup.check_duplicate(arabic: str, translation_ru: str) -> DuplicateCheck` — синхронная; из бота вызывается через `sync_to_async`.

- [ ] **Step 1: Написать падающие тесты**

`tests/services/test_dedup.py`:

```python
import pytest

from vocabulary.enums import Kind, Person, Source
from vocabulary.models import Entry
from vocabulary.services.dedup import DuplicateKind, check_duplicate

pytestmark = pytest.mark.django_db


def make_word(arabic: str, translation: str) -> Entry:
    return Entry.objects.create(
        kind=Kind.WORD, arabic=arabic, translation_ru=translation, source=Source.TEXTBOOK
    )


def test_unknown_entry_is_new() -> None:
    result = check_duplicate("كِتَاب", "книга")

    assert result.kind is DuplicateKind.NONE
    assert result.existing_id is None


def test_identical_entry_is_exact() -> None:
    word = make_word("كِتَاب", "книга")

    result = check_duplicate("كِتَاب", "книга")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_id == word.id


def test_translation_comparison_ignores_case_and_spaces() -> None:
    word = make_word("بَيْت", "дом")

    result = check_duplicate("بَيْت", "  Дом ")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_id == word.id


def test_other_harakat_same_translation_is_similar_with_flag() -> None:
    # Most likely the same word re-imported with different harakat — skip it.
    word = make_word("مُدَرِّس", "учитель")

    result = check_duplicate("مُدَرِّسٌ", "учитель")

    assert result.kind is DuplicateKind.SIMILAR
    assert result.same_translation is True
    assert result.existing_id == word.id


def test_gender_pair_is_similar_without_flag() -> None:
    # Same skeleton, different translation: the feminine counterpart, must be added.
    masculine = Entry.objects.create(
        kind=Kind.PHRASE,
        arabic="مَا اسْمُكَ؟",
        translation_ru="как тебя зовут? (к мужчине)",
        person=Person.ANTA,
        source=Source.MANUAL,
    )

    result = check_duplicate("مَا اسْمُكِ؟", "как тебя зовут? (к женщине)")

    assert result.kind is DuplicateKind.SIMILAR
    assert result.same_translation is False
    assert result.existing_id == masculine.id
    assert result.existing_arabic == "مَا اسْمُكَ؟"


def test_homograph_is_similar_without_flag() -> None:
    make_word("عَيْن", "глаз")

    result = check_duplicate("عَيْن", "источник")

    assert result.kind is DuplicateKind.SIMILAR
    assert result.same_translation is False


def test_exact_wins_over_similar() -> None:
    make_word("عَيْن", "глаз")
    expected = make_word("عَيْن", "источник")

    result = check_duplicate("عَيْن", "источник")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_id == expected.id


def test_same_translation_candidate_is_preferred_in_report() -> None:
    make_word("مُدَرِّس", "преподаватель")
    same_translation = make_word("مُدَرِّسٌ", "учитель")

    result = check_duplicate("مُدَرِّسْ", "учитель")

    assert result.kind is DuplicateKind.SIMILAR
    assert result.same_translation is True
    assert result.existing_id == same_translation.id
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_dedup.py -q 2>&1 | tail -5`
Expected: FAIL — `ModuleNotFoundError: No module named 'vocabulary.services.dedup'`.

- [ ] **Step 3: Реализовать поиск**

`vocabulary/services/dedup.py`:

```python
"""Classify an incoming entry against the shared deck. See spec 4.2."""

from dataclasses import dataclass
from enum import StrEnum

from vocabulary.models import Entry
from vocabulary.services.arabic import normalize_arabic


class DuplicateKind(StrEnum):
    NONE = "none"
    EXACT = "exact"
    # Same skeleton, but not the same exact arabic or not the same translation.
    SIMILAR = "similar"


@dataclass(frozen=True)
class DuplicateCheck:
    kind: DuplicateKind
    existing_id: int | None = None
    existing_arabic: str | None = None
    existing_translation: str | None = None
    # True when the found entry has the same translation, which usually means the
    # same word re-imported with different harakat. False points at a gender
    # counterpart or a homograph — content that should be added.
    same_translation: bool = False


def _same_translation(left: str, right: str) -> bool:
    return left.strip().casefold() == right.strip().casefold()


def check_duplicate(arabic: str, translation_ru: str) -> DuplicateCheck:
    """Look up near-duplicates by normalized skeleton, then compare exact arabic.

    Synchronous: the bot calls it through asgiref.sync.sync_to_async.
    """
    candidates = list(Entry.objects.filter(arabic_norm=normalize_arabic(arabic)))
    if not candidates:
        return DuplicateCheck(DuplicateKind.NONE)

    matching = [c for c in candidates if _same_translation(c.translation_ru, translation_ru)]

    for candidate in matching:
        if candidate.arabic == arabic:
            return DuplicateCheck(
                DuplicateKind.EXACT,
                candidate.id,
                candidate.arabic,
                candidate.translation_ru,
                same_translation=True,
            )

    # Report the most informative candidate: one with the same translation when there
    # is one, since that is the case where skipping is usually right.
    reported = (matching or candidates)[0]
    return DuplicateCheck(
        DuplicateKind.SIMILAR,
        reported.id,
        reported.arabic,
        reported.translation_ru,
        same_translation=bool(matching),
    )
```

- [ ] **Step 4: Прогнать тесты**

Run: `uv run pytest tests/services/test_dedup.py -q 2>&1 | tail -3`
Expected: 8 passed.

- [ ] **Step 5: Закоммитить**

```bash
git add vocabulary/services/dedup.py tests/services/test_dedup.py
git commit -m "feat: classify imported entries as new, exact duplicate or similar"
```

**Проверка задачи для владельца:** слово с другими огласовками и тем же переводом помечается как похожее с флагом «перевод совпадает»; женская форма фразы — как похожее без флага, то есть предлагается добавить.

---

### Task 7: Файл поведения ИИ и его загрузчик

**Files:**
- Create: `content/curriculum.yaml`
- Create: `vocabulary/services/curriculum.py`
- Test: `tests/services/test_curriculum.py`

**Interfaces:**
- Consumes: `vocabulary.enums.Person`.
- Produces:
  - `vocabulary.services.curriculum.Curriculum` — `rules: Rules`, `topics: list[Topic]`; методы `enabled_topics() -> list[Topic]`, `topic(topic_id: str) -> Topic`.
  - `Rules` — `language_register: str` (в YAML ключ `register`), `harakat: str`, `max_new_words_per_sentence: int`, `forms_per_entry: int`, `pronouns: list[str]`, `service_words: list[str]`.
  - `Topic` — `id`, `title`, `enabled`, `target_count`, `ask_for: list[str]`, `examples: list[Example]`; `Example` — `ar: str`, `ru: str`.
  - `load_curriculum(path: Path | None = None) -> Curriculum`.

- [ ] **Step 1: Создать файл содержания**

`content/curriculum.yaml`:

```yaml
# Файл поведения ИИ. Меняется без правки кода.
#
# Главный рычаг — examples: модель ловит стиль по образцам точнее, чем по описанию.
# Нужна другая выдача по теме — допиши в неё пример.
#
# pronouns управляет сразу двумя вещами: какие лица генерировать в формах слов и
# какие использовать во фразах. Прошли новое местоимение — допиши строку.

rules:
  register: msa                      # литературный арабский, по «العربية بين يديك»
  harakat: required                  # огласовки обязательны везде
  max_new_words_per_sentence: 1      # больше одного нового слова на предложение нельзя
  forms_per_entry: 2                 # сколько форм просить у ИИ на одно слово
  pronouns: [ana, huwa, hiya, anta, anti, nahnu]
  service_words:                     # служебные слова, разрешённые всегда
    - فِي
    - مِنْ
    - إِلَى
    - هَذَا
    - هَذِهِ
    - مَا
    - مَاذَا
    - أَيْنَ

topics:
  - id: introductions
    title: Знакомство
    enabled: true
    target_count: 12
    ask_for:
      - вопрос и ответ об имени
      - вопрос и ответ о происхождении
    examples:
      - ar: مَا اسْمُكَ؟
        ru: как тебя зовут? (к мужчине)
      - ar: مَا اسْمُكِ؟
        ru: как тебя зовут? (к женщине)
      - ar: مِنْ أَيْنَ أَنْتَ؟
        ru: откуда ты? (к мужчине)

  - id: daily_activity
    title: Чем занимаешься
    enabled: true
    target_count: 10
    ask_for:
      - вопрос о текущем занятии
      - ответ о текущем занятии
    examples:
      - ar: مَاذَا تَفْعَلُ؟
        ru: что ты делаешь? (к мужчине)
      - ar: مَاذَا تَفْعَلِينَ؟
        ru: что ты делаешь? (к женщине)

  # Пример выключенной темы: остаётся в файле, но не используется.
  - id: shopping
    title: Покупки
    enabled: false
    target_count: 10
    ask_for:
      - вопрос о цене
    examples: []
```

- [ ] **Step 2: Написать падающие тесты**

`tests/services/test_curriculum.py`:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from vocabulary.services.curriculum import load_curriculum

VALID = """
rules:
  register: msa
  harakat: required
  max_new_words_per_sentence: 1
  forms_per_entry: 2
  pronouns: [ana, anta, anti]
  service_words: [فِي]
topics:
  - id: introductions
    title: Знакомство
    enabled: true
    target_count: 12
    ask_for: [вопрос об имени]
    examples:
      - ar: مَا اسْمُكَ؟
        ru: как тебя зовут? (к мужчине)
  - id: shopping
    title: Покупки
    enabled: false
    target_count: 5
    ask_for: [вопрос о цене]
    examples: []
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "curriculum.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_valid_file(tmp_path: Path) -> None:
    curriculum = load_curriculum(write(tmp_path, VALID))

    assert curriculum.rules.forms_per_entry == 2
    assert curriculum.rules.pronouns == ["ana", "anta", "anti"]
    assert len(curriculum.topics) == 2


def test_enabled_topics_skips_disabled(tmp_path: Path) -> None:
    curriculum = load_curriculum(write(tmp_path, VALID))

    assert [topic.id for topic in curriculum.enabled_topics()] == ["introductions"]


def test_topic_lookup_by_id(tmp_path: Path) -> None:
    curriculum = load_curriculum(write(tmp_path, VALID))

    assert curriculum.topic("introductions").title == "Знакомство"


def test_unknown_topic_id_raises(tmp_path: Path) -> None:
    curriculum = load_curriculum(write(tmp_path, VALID))

    with pytest.raises(KeyError, match="nope"):
        curriculum.topic("nope")


def test_unknown_pronoun_is_rejected(tmp_path: Path) -> None:
    text = VALID.replace("[ana, anta, anti]", "[ana, hum]")

    with pytest.raises(ValidationError, match="hum"):
        load_curriculum(write(tmp_path, text))


def test_duplicate_topic_id_is_rejected(tmp_path: Path) -> None:
    text = VALID.replace("id: shopping", "id: introductions")

    with pytest.raises(ValidationError, match="introductions"):
        load_curriculum(write(tmp_path, text))


def test_enabled_topic_without_examples_is_rejected(tmp_path: Path) -> None:
    # Examples are the main steering lever, so an active topic must have one.
    text = VALID.replace(
        """    examples:
      - ar: مَا اسْمُكَ؟
        ru: как тебя зовут? (к мужчине)""",
        "    examples: []",
    )

    with pytest.raises(ValidationError, match="introductions"):
        load_curriculum(write(tmp_path, text))


def test_typo_in_field_name_is_rejected(tmp_path: Path) -> None:
    # extra="forbid" turns a silent no-op into a clear error.
    text = VALID.replace("forms_per_entry: 2", "forms_per_entrys: 2")

    with pytest.raises(ValidationError):
        load_curriculum(write(tmp_path, text))


def test_shipped_file_is_valid() -> None:
    curriculum = load_curriculum()

    assert curriculum.rules.language_register == "msa"
    assert "anti" in curriculum.rules.pronouns
    assert curriculum.enabled_topics()
```

- [ ] **Step 3: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_curriculum.py -q 2>&1 | tail -5`
Expected: FAIL — `ModuleNotFoundError: No module named 'vocabulary.services.curriculum'`.

- [ ] **Step 4: Реализовать загрузчик**

`vocabulary/services/curriculum.py`:

```python
"""Loader for content/curriculum.yaml — the editable description of AI behaviour.

Validated through pydantic so a typo in the file produces a clear error instead of a
strange prompt.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from vocabulary.enums import Person

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "content" / "curriculum.yaml"

_VALID_PRONOUNS = {choice.value for choice in Person}


class Example(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ar: str
    ru: str


class Rules(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # Aliased: the YAML key stays "register" (the linguistic term), but a field of
    # that name would shadow ABCMeta.register inherited by BaseModel and make
    # pydantic emit a warning on every import.
    language_register: str = Field(alias="register")
    harakat: Literal["required", "optional"] = "required"
    max_new_words_per_sentence: int = Field(default=1, ge=0)
    forms_per_entry: int = Field(default=2, ge=0)
    pronouns: list[str] = Field(min_length=1)
    service_words: list[str] = []

    @model_validator(mode="after")
    def _check_pronouns(self) -> Self:
        unknown = [name for name in self.pronouns if name not in _VALID_PRONOUNS]
        if unknown:
            allowed = ", ".join(sorted(_VALID_PRONOUNS))
            raise ValueError(f"unknown pronouns: {', '.join(unknown)}; allowed: {allowed}")
        return self


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    enabled: bool = True
    target_count: int = Field(ge=1)
    ask_for: list[str] = Field(min_length=1)
    examples: list[Example] = []


class Curriculum(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: Rules
    topics: list[Topic] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_topics(self) -> Self:
        seen: set[str] = set()
        for topic in self.topics:
            if topic.id in seen:
                raise ValueError(f"duplicate topic id: {topic.id}")
            seen.add(topic.id)
            # Examples are the main steering lever; an active topic without one
            # would produce unguided output.
            if topic.enabled and not topic.examples:
                raise ValueError(f"enabled topic without examples: {topic.id}")
        return self

    def enabled_topics(self) -> list[Topic]:
        return [topic for topic in self.topics if topic.enabled]

    def topic(self, topic_id: str) -> Topic:
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        raise KeyError(f"unknown topic: {topic_id}")


def load_curriculum(path: Path | None = None) -> Curriculum:
    raw = yaml.safe_load((path or DEFAULT_PATH).read_text(encoding="utf-8"))
    return Curriculum.model_validate(raw)
```

- [ ] **Step 5: Прогнать тесты**

Run: `uv run pytest tests/services/test_curriculum.py -q 2>&1 | tail -3`
Expected: 9 passed.

- [ ] **Step 6: Закоммитить**

```bash
git add content vocabulary/services/curriculum.py tests/services/test_curriculum.py
git commit -m "feat: validated curriculum file driving AI content generation"
```

**Проверка задачи для владельца:** впиши в `content/curriculum.yaml` опечатку в имени поля или несуществующее местоимение — `uv run pytest tests/services/test_curriculum.py::test_shipped_file_is_valid` упадёт с внятным сообщением.

---

### Task 8: Сидер и README

**Files:**
- Create: `vocabulary/management/__init__.py`, `vocabulary/management/commands/__init__.py`, `vocabulary/management/commands/seed_deck.py`
- Create: `README.md`

**Interfaces:**
- Consumes: модели, `match_entries_in_sentence`.
- Produces: команда `uv run python manage.py seed_deck` — идемпотентная.

- [ ] **Step 1: Написать команду**

Создать `vocabulary/management/__init__.py` и `vocabulary/management/commands/__init__.py` пустыми.

`vocabulary/management/commands/seed_deck.py`:

```python
"""Seed the shared deck with a small textbook-like sample.

Idempotent: re-running adds nothing. Covers all three kinds of study unit so the
queues have something realistic to work with.
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from vocabulary.enums import Kind, Person, Pos, Source, Tense
from vocabulary.models import Entry, Sentence, SentenceEntry
from vocabulary.services.arabic import match_entries_in_sentence

# (arabic, russian, transliteration, topic, part of speech)
WORDS: list[tuple[str, str, str, str, str]] = [
    ("بَيْت", "дом", "bayt", "быт", Pos.NOUN),
    ("كِتَاب", "книга", "kitab", "учёба", Pos.NOUN),
    ("مَدْرَسَة", "школа", "madrasa", "учёба", Pos.NOUN),
    ("مُدَرِّس", "учитель", "mudarris", "учёба", Pos.NOUN),
    ("طَالِب", "студент", "talib", "учёба", Pos.NOUN),
    ("قَلَم", "ручка", "qalam", "учёба", Pos.NOUN),
    ("مَاء", "вода", "ma'", "еда", Pos.NOUN),
    ("خُبْز", "хлеб", "khubz", "еда", Pos.NOUN),
    ("بَاب", "дверь", "bab", "быт", Pos.NOUN),
    ("وَلَد", "мальчик", "walad", "люди", Pos.NOUN),
    ("بِنْت", "девочка", "bint", "люди", Pos.NOUN),
    ("رَجُل", "мужчина", "rajul", "люди", Pos.NOUN),
    ("اِمْرَأَة", "женщина", "imra'a", "люди", Pos.NOUN),
    ("صَدِيق", "друг", "sadiq", "люди", Pos.NOUN),
    ("مَدِينَة", "город", "madina", "город", Pos.NOUN),
    ("سَيَّارَة", "машина", "sayyara", "город", Pos.NOUN),
    ("شَمْس", "солнце", "shams", "природа", Pos.NOUN),
    ("قَمَر", "луна", "qamar", "природа", Pos.NOUN),
    ("يَوْم", "день", "yawm", "время", Pos.NOUN),
    ("كَبِير", "большой", "kabir", "признаки", ""),
    ("كَتَبَ", "писать", "kataba", "учёба", Pos.VERB),
]

# (arabic, russian, transliteration, base arabic, person, tense)
FORMS: list[tuple[str, str, str, str, str, str]] = [
    ("سَيَّارَتُهُ", "его машина", "sayyaratuhu", "سَيَّارَة", Person.HUWA, ""),
    ("سَيَّارَتُهَا", "её машина", "sayyaratuha", "سَيَّارَة", Person.HIYA, ""),
    ("كِتَابِي", "моя книга", "kitabi", "كِتَاب", Person.ANA, ""),
    ("كِتَابُكَ", "твоя книга (к мужчине)", "kitabuka", "كِتَاب", Person.ANTA, ""),
    ("أَكْتُبُ", "я пишу", "aktubu", "كَتَبَ", Person.ANA, Tense.PRESENT),
    ("يَكْتُبُ", "он пишет", "yaktubu", "كَتَبَ", Person.HUWA, Tense.PRESENT),
]

# (arabic, russian, transliteration, person)
PHRASES: list[tuple[str, str, str, str]] = [
    ("مَا اسْمُكَ؟", "как тебя зовут? (к мужчине)", "ma ismuka?", Person.ANTA),
    ("مَا اسْمُكِ؟", "как тебя зовут? (к женщине)", "ma ismuki?", Person.ANTI),
    ("مِنْ أَيْنَ أَنْتَ؟", "откуда ты? (к мужчине)", "min ayna anta?", Person.ANTA),
    ("مِنْ أَيْنَ أَنْتِ؟", "откуда ты? (к женщине)", "min ayna anti?", Person.ANTI),
    ("مَاذَا تَفْعَلُ؟", "что ты делаешь? (к мужчине)", "madha taf'alu?", Person.ANTA),
]

SENTENCES: list[tuple[str, str]] = [
    ("هَذَا بَيْتٌ كَبِيرٌ", "Это большой дом."),
    ("الْمُدَرِّسُ فِي الْمَدْرَسَةِ", "Учитель в школе."),
    ("الْوَلَدُ يَشْرَبُ الْمَاءَ", "Мальчик пьёт воду."),
    ("هَذَا قَلَمُ الطَّالِبِ", "Это ручка студента."),
    ("الشَّمْسُ وَالْقَمَرُ", "Солнце и луна."),
]


class Command(BaseCommand):
    help = "Наполнить общую колоду учебным набором слов, фраз и форм"

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        words = self._seed_words()
        forms = self._seed_forms()
        phrases = self._seed_phrases()
        sentences, links = self._seed_sentences()

        self.stdout.write(
            f"words +{words}, forms +{forms}, phrases +{phrases}, "
            f"sentences +{sentences}, links +{links}"
        )

    def _seed_words(self) -> int:
        added = 0
        for arabic, translation, translit, topic, pos in WORDS:
            _, created = Entry.objects.get_or_create(
                arabic=arabic,
                translation_ru=translation,
                defaults={
                    "kind": Kind.WORD,
                    "transliteration": translit,
                    "topic": topic,
                    "pos": pos,
                    "source": Source.TEXTBOOK,
                },
            )
            added += int(created)
        return added

    def _seed_forms(self) -> int:
        added = 0
        for arabic, translation, translit, base_arabic, person, tense in FORMS:
            base = Entry.objects.get(arabic=base_arabic, kind=Kind.WORD)
            _, created = Entry.objects.get_or_create(
                arabic=arabic,
                translation_ru=translation,
                defaults={
                    "kind": Kind.FORM,
                    "transliteration": translit,
                    "base": base,
                    "person": person,
                    "tense": tense,
                    "topic": base.topic,
                    "source": Source.MANUAL,
                },
            )
            added += int(created)
        return added

    def _seed_phrases(self) -> int:
        added = 0
        for arabic, translation, translit, person in PHRASES:
            _, created = Entry.objects.get_or_create(
                arabic=arabic,
                translation_ru=translation,
                defaults={
                    "kind": Kind.PHRASE,
                    "transliteration": translit,
                    "person": person,
                    "topic": "знакомство",
                    "source": Source.MANUAL,
                },
            )
            added += int(created)
        return added

    def _seed_sentences(self) -> tuple[int, int]:
        known = {entry.arabic_norm: entry.id for entry in Entry.objects.all()}
        added_sentences = 0
        added_links = 0
        for arabic, translation in SENTENCES:
            sentence, created = Sentence.objects.get_or_create(
                arabic=arabic,
                defaults={"translation_ru": translation, "source": Source.TEXTBOOK},
            )
            added_sentences += int(created)
            for entry_id in match_entries_in_sentence(arabic, known):
                _, link_created = SentenceEntry.objects.get_or_create(
                    sentence=sentence, entry_id=entry_id
                )
                added_links += int(link_created)
        return added_sentences, added_links
```

- [ ] **Step 2: Запустить сидер**

Run: `uv run python manage.py seed_deck`
Expected: ровно `words +21, forms +6, phrases +5, sentences +5, links +10` (числа посчитаны прогоном логики сопоставления на этих данных).

- [ ] **Step 3: Проверить идемпотентность**

Run: `uv run python manage.py seed_deck`
Expected: `words +0, forms +0, phrases +0, sentences +0, links +0`.

- [ ] **Step 4: Проверить данные в БД**

Run:
```bash
docker compose exec db psql -U mufradat -d mufradat -c \
  "select kind, count(*) from vocabulary_entry group by kind order by kind;"
```
Expected: `form 6`, `phrase 5`, `word 21`.

Run:
```bash
docker compose exec db psql -U mufradat -d mufradat -c \
  "select s.translation_ru, count(se.entry_id) as entries
   from vocabulary_sentence s
   left join vocabulary_sentenceentry se on se.sentence_id = s.id
   group by s.id, s.translation_ru order by s.id;"
```
Expected: у каждого из пяти примеров по 2 связанные единицы.

- [ ] **Step 5: Написать README**

`README.md`:

````markdown
# Mufradat Bot

Telegram Mini App для заучивания арабских слов группой из ~10 человек. Общая колода
на всех: админ наполняет базу, остальные учат по карточкам с интервальным
повторением (FSRS). Прогресс у каждого свой.

Дизайн: `docs/superpowers/specs/2026-08-05-mufradat-bot-design.md`.

## Требования

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker (для Postgres 16)

## Локальный запуск

```bash
cp .env.example .env         # заполнить значения; порт 5433, чтобы не мешать локальному Postgres
docker compose up -d
uv sync --extra dev
uv run python manage.py migrate
uv run python manage.py seed_deck
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Админка: `http://127.0.0.1:8000/admin/`.

## Тесты

```bash
uv run pytest            # весь набор
uv run ruff check .      # линтер
```

Тестовую базу `pytest-django` создаёт и удаляет сам.

## Что где лежит

| Путь | Ответственность |
|---|---|
| `mufradat/config.py` | настройки из `.env`, гейтинг админа |
| `mufradat/settings.py` | настройки Django, собирает `DATABASES` из конфига |
| `vocabulary/models.py` | `Entry` (слова, фразы, формы), примеры, прогресс, история |
| `vocabulary/admin.py` | админка для правки базы без кода |
| `vocabulary/services/arabic.py` | нормализация, сопоставление слов предложения |
| `vocabulary/services/dedup.py` | поиск похожих записей при импорте |
| `vocabulary/services/curriculum.py` | загрузчик `content/curriculum.yaml` |
| `content/curriculum.yaml` | **поведение ИИ: темы, правила, примеры** |

## Как менять поведение ИИ

Правится `content/curriculum.yaml`, код не трогается. Главный рычаг — блок
`examples` внутри темы: модель ловит стиль по образцам точнее, чем по описанию.
Список `pronouns` управляет и формами слов, и лицами во фразах.

Проверить файл после правки:

```bash
uv run pytest tests/services/test_curriculum.py -q
```
````

- [ ] **Step 6: Прогнать весь набор и линтер**

Run: `uv run pytest -q 2>&1 | tail -3 && uv run ruff format . && uv run ruff check .`
Expected: 66 passed, линтер без ошибок.

- [ ] **Step 7: Закоммитить**

```bash
git add vocabulary/management README.md
git commit -m "feat: idempotent deck seeder and project README"
```

**Проверка задачи для владельца:** `manage.py seed_deck` заливает 21 слово, 6 форм, 5 фраз, 5 примеров и 10 связок; повторный запуск ничего не добавляет; в админке видны все три типа единиц.

---

## Что дальше

Следующие планы пишутся по одному, после одобрения предыдущего:

| План | Содержание | Этап спеки |
|---|---|---|
| 2 | Скелет бота: `/start` печатает Telegram ID, роли, `/help` | 3 |
| 3 | Ручной ввод `/add`: слова и фразы с занятий | 4 |
| 4 | Импорт по фото: vision, дедупликация, подтверждение | 5 |
| 5 | Картинки: Openverse, своё фото, атрибуция | 6 |
| 6 | DRF: аутентификация по `initData`, очереди, FSRS | 7 |
| 7 | Mini App на Vue 3: три режима, карточки | 8 |
| 8 | Словоформы `/forms` и генерация по темам | 9 |
| 9 | Полировка | 10 |
