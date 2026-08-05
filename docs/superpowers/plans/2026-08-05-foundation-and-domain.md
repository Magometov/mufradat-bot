# Mufradat Bot — план 1: фундамент и домен

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Поднять каркас проекта с рабочей БД, схемой данных и протестированной логикой обработки арабского текста — фундамент, на который встанут бот, API и Mini App.

**Architecture:** Один Python-пакет `app/` с чётким разделением: `config.py` (настройки из `.env`), `db/` (модели и сессии), `services/` (чистая логика домена). Никакого бота и API на этом плане — только то, от чего они зависят. Логика обработки арабского живёт в `services/arabic.py` как чистые функции без БД, поэтому тестируется быстро и полностью. Всё, что требует БД, тестируется на реальном Postgres 16 в Docker с откатом транзакции после каждого теста.

**Tech Stack:** Python 3.12, SQLAlchemy 2.0 (async) + asyncpg, Alembic, pydantic-settings, pytest + pytest-asyncio, Postgres 16 в Docker, uv для зависимостей.

Покрывает этапы 1–2 спеки `docs/superpowers/specs/2026-08-05-mufradat-bot-design.md`.

## Global Constraints

- Python 3.12 (`requires-python = ">=3.12,<3.13"`). Зависимости ставятся через `uv sync`.
- Идентификаторы и комментарии в коде — на английском. Текст, который видит пользователь (сообщения бота, интерфейс) — на русском. В этом плане пользовательского текста нет, кроме данных сидера.
- Локальный Postgres 14 не трогаем: контейнер слушает **порт 5433**.
- Никаких секретов в коде. `.env` в `.gitignore`, рядом `.env.example`.
- Версии зависимостей (проверены на PyPI 2026-08-05): `sqlalchemy>=2.0.51,<2.1`, `alembic>=1.19,<2`, `asyncpg>=0.31,<0.32`, `pydantic-settings>=2.14,<3`, `pytest>=9.1,<10`, `pytest-asyncio>=1.4,<2`, `ruff>=0.16,<0.17`. Зависимости для бота, API и ИИ добавляются в своих планах, не здесь.
- Все временные метки в БД — `TIMESTAMPTZ` (`DateTime(timezone=True)`).
- Арабский в тестах и сидере — реальный, с огласовками.
- Каждая задача заканчивается коммитом. После каждой задачи — стоп и одобрение владельца.

---

### Task 1: Каркас проекта, конфигурация и соединение с БД

**Files:**
- Create: `pyproject.toml`
- Create: `docker-compose.yml`
- Create: `docker/init-test-db.sql`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `app/__init__.py`, `app/config.py`
- Create: `app/db/__init__.py`, `app/db/base.py`, `app/db/session.py`
- Create: `scripts/check_db.py`
- Test: `tests/__init__.py`, `tests/test_config.py`

**Interfaces:**
- Consumes: ничего (первая задача).
- Produces:
  - `app.config.Settings` — pydantic-модель настроек с полями `database_url: str`, `test_database_url: str`, `bot_token: SecretStr | None`, `anthropic_api_key: SecretStr | None`, `ai_model: str`, `webapp_url: str | None`, `admin_telegram_ids: list[int]`.
  - `app.config.get_settings() -> Settings` — кэширующий геттер (`lru_cache`), в тестах сбрасывается через `get_settings.cache_clear()`.
  - `app.db.base.Base` — декларативная база SQLAlchemy, `Base.metadata` используется Alembic и тестами.
  - `app.db.session.get_engine() -> AsyncEngine` и `app.db.session.get_sessionmaker() -> async_sessionmaker[AsyncSession]`.

- [ ] **Step 1: Запустить Docker Desktop**

Docker-демон сейчас не поднят. Запустить Docker Desktop и дождаться готовности:

Run: `docker info --format '{{.ServerVersion}}'`
Expected: печатает версию сервера (не пусто и не ошибка).

- [ ] **Step 2: Создать `pyproject.toml` и пустые пакеты**

Пакеты создаются сразу: `uv sync` собирает `app` как editable-пакет и упадёт с
`Unable to determine which files to ship`, если каталога ещё нет.

Run: `mkdir -p app/db app/services scripts tests/db tests/services docker && touch app/__init__.py app/db/__init__.py app/services/__init__.py tests/__init__.py tests/db/__init__.py tests/services/__init__.py`
Expected: каталоги и пустые `__init__.py` созданы.

```toml
[project]
name = "mufradat-bot"
version = "0.1.0"
description = "Telegram Mini App for learning Arabic vocabulary with spaced repetition"
requires-python = ">=3.12,<3.13"
dependencies = [
    "sqlalchemy[asyncio]>=2.0.51,<2.1",
    "alembic>=1.19,<2",
    "asyncpg>=0.31,<0.32",
    "pydantic-settings>=2.14,<3",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.1,<10",
    "pytest-asyncio>=1.4,<2",
    "ruff>=0.16,<0.17",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 3: Создать `.gitignore` и `.env.example`**

`.gitignore`:

```
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.env
node_modules/
dist/
```

`.env.example`:

```
# Postgres в Docker слушает 5433, чтобы не конфликтовать с локальным Postgres 14
DATABASE_URL=postgresql+asyncpg://mufradat:mufradat@localhost:5433/mufradat

# Заполняется на этапе бота: /start печатает твой Telegram ID
BOT_TOKEN=
ADMIN_TELEGRAM_IDS=

# Заполняется на этапе импорта по фото
ANTHROPIC_API_KEY=
AI_MODEL=claude-sonnet-5

# HTTPS-адрес Mini App (в разработке — туннель cloudflared)
WEBAPP_URL=
```

- [ ] **Step 4: Создать `docker-compose.yml` и init-скрипт тестовой БД**

`docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: mufradat-db
    environment:
      POSTGRES_USER: mufradat
      POSTGRES_PASSWORD: mufradat
      POSTGRES_DB: mufradat
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/init-test-db.sql:/docker-entrypoint-initdb.d/init-test-db.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mufradat -d mufradat"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
```

`docker/init-test-db.sql`:

```sql
-- Separate database for the test suite; created once on first container start.
CREATE DATABASE mufradat_test OWNER mufradat;
```

- [ ] **Step 5: Поднять контейнер и проверить готовность**

Run: `cp .env.example .env && docker compose up -d && docker compose ps`
Expected: сервис `db` в состоянии `running (healthy)` (healthy появляется через ~5-10 секунд, при необходимости повторить `docker compose ps`).

- [ ] **Step 6: Написать падающий тест конфигурации**

`tests/test_config.py`:

```python
from app.config import Settings

DSN = "postgresql+asyncpg://u:p@localhost:5433/mufradat"


def test_admin_ids_parsed_from_comma_separated_string() -> None:
    settings = Settings(database_url=DSN, admin_telegram_ids="111,222", _env_file=None)

    assert settings.admin_telegram_ids == [111, 222]


def test_admin_ids_tolerate_spaces_and_trailing_comma() -> None:
    settings = Settings(database_url=DSN, admin_telegram_ids=" 111 , 222 , ", _env_file=None)

    assert settings.admin_telegram_ids == [111, 222]


def test_admin_ids_empty_string_gives_empty_list() -> None:
    settings = Settings(database_url=DSN, admin_telegram_ids="", _env_file=None)

    assert settings.admin_telegram_ids == []


def test_test_database_url_derived_from_database_url() -> None:
    settings = Settings(database_url=DSN, _env_file=None)

    assert settings.test_database_url == DSN + "_test"


def test_explicit_test_database_url_wins() -> None:
    settings = Settings(database_url=DSN, test_database_url="postgresql+asyncpg://x/y", _env_file=None)

    assert settings.test_database_url == "postgresql+asyncpg://x/y"


def test_ai_model_has_default() -> None:
    settings = Settings(database_url=DSN, _env_file=None)

    assert settings.ai_model == "claude-sonnet-5"


def test_secrets_are_not_exposed_in_repr() -> None:
    settings = Settings(database_url=DSN, bot_token="123:secret", _env_file=None)

    assert "secret" not in repr(settings)
    assert settings.bot_token is not None
    assert settings.bot_token.get_secret_value() == "123:secret"
```

- [ ] **Step 7: Установить зависимости и убедиться, что тест падает**

Run: `uv sync --extra dev && uv run pytest tests/test_config.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'app.config'` (или `ImportError`).

- [ ] **Step 8: Реализовать `app/config.py`**

```python
from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    # Defaults to database_url + "_test" (see _derive_test_database_url).
    test_database_url: str = ""

    bot_token: SecretStr | None = None
    admin_telegram_ids: list[int] = []

    anthropic_api_key: SecretStr | None = None
    ai_model: str = "claude-sonnet-5"

    webapp_url: str | None = None

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        """Accept a comma-separated string, since .env cannot hold a JSON list comfortably."""
        if isinstance(value, str):
            return [int(part) for part in value.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def _derive_test_database_url(self) -> "Settings":
        if not self.test_database_url:
            self.test_database_url = f"{self.database_url}_test"
        return self

    def is_admin(self, telegram_id: int) -> bool:
        """Single place where admin rights are decided."""
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from env / .env
```

- [ ] **Step 9: Убедиться, что тесты конфигурации проходят**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS, 7 тестов.

- [ ] **Step 10: Создать базу SQLAlchemy и фабрику сессий**

`app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base. Base.metadata is the single source of truth for Alembic."""
```

`app/db/session.py`:

```python
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)
```

- [ ] **Step 11: Написать скрипт проверки соединения**

`scripts/check_db.py`:

```python
"""Smoke check: connect to the database and print its version."""

import asyncio

from sqlalchemy import text

from app.db.session import get_engine


async def main() -> None:
    engine = get_engine()
    async with engine.connect() as connection:
        version = (await connection.execute(text("select version()"))).scalar_one()
    print(version)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 12: Проверить соединение с обеими базами**

Run: `uv run python scripts/check_db.py`
Expected: печатает строку вида `PostgreSQL 16.x ...`.

Run: `docker compose exec db psql -U mufradat -lqt | cut -d'|' -f1 | grep -E 'mufradat(_test)?'`
Expected: в списке есть и `mufradat`, и `mufradat_test`.

- [ ] **Step 13: Проверить линтер и закоммитить**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: без ошибок (при необходимости выполнить `uv run ruff format .`).

```bash
git add pyproject.toml uv.lock docker-compose.yml docker/ .gitignore .env.example app/ scripts/ tests/
git commit -m "feat: project skeleton with settings, async DB session and Postgres 16 container"
```

**Проверка задачи для владельца:** `docker compose ps` показывает healthy, `uv run python scripts/check_db.py` печатает версию Postgres 16, `uv run pytest` — зелёный.

---

### Task 2: Нормализация арабского текста

Основа дедупликации: одно и то же слово, распознанное с разной расстановкой харакат, должно приводиться к одной форме.

**Files:**
- Create: `app/services/arabic.py`
- Test: `tests/services/test_arabic.py`

**Interfaces:**
- Consumes: ничего (чистая логика, без БД и настроек).
- Produces: `app.services.arabic.normalize_arabic(text: str) -> str`.

- [ ] **Step 1: Написать падающие тесты**

`tests/services/test_arabic.py`:

```python
from app.services.arabic import normalize_arabic


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
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_arabic.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'app.services'`.

- [ ] **Step 3: Реализовать нормализацию**

`app/services/arabic.py`:

```python
"""Pure text helpers for Arabic. No database, no settings — trivially testable."""

import re
import unicodedata

# Harakat, tanwin, shadda, sukun, superscript alef and Quranic marks.
_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")

_TATWEEL = "\u0640"  # tatweel, a purely decorative letter-stretching mark

# Alef variants collapse to bare alef; alef maqsura collapses to ya.
# ta marbuta (ة) is deliberately NOT merged into ha (ه): it changes meaning.
_LETTER_FOLDING = str.maketrans(
    {
        "\u0623": "\u0627",  # alef with hamza above -> alef
        "\u0625": "\u0627",  # alef with hamza below -> alef
        "\u0622": "\u0627",  # alef with madda above -> alef
        "\u0671": "\u0627",  # alef wasla -> alef
        "\u0649": "\u064A",  # alef maqsura -> ya
    }
)


def normalize_arabic(text: str) -> str:
    """Reduce an Arabic string to a comparison key.

    Diacritics are how the textbook teaches pronunciation, so they are stored as
    recognised — but they must not participate in duplicate detection: the vision
    model may return the same word with slightly different harakat.
    """
    text = unicodedata.normalize("NFC", text)
    text = _DIACRITICS.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = text.translate(_LETTER_FOLDING)
    return " ".join(text.split())
```

- [ ] **Step 4: Убедиться, что тесты проходят**

Run: `uv run pytest tests/services/test_arabic.py -v`
Expected: PASS, 12 тестов.

- [ ] **Step 5: Закоммитить**

```bash
git add app/services/ tests/services/
git commit -m "feat: normalize Arabic text for duplicate detection"
```

**Проверка задачи для владельца:** `uv run pytest tests/services/test_arabic.py -v` — зелёный, все 12 кейсов.

---

### Task 3: Сопоставление слов предложения со словарём

Нужно, чтобы связать `sentences` с `words` через `sentence_words`. Наивное сравнение не работает: в тексте слово идёт с артиклем `ال` и слитными предлогами/союзами (`و`, `ف`, `ب`, `ل`, `ك`), поэтому `الْكِتَابُ` не совпадёт с `كِتَاب`.

**Files:**
- Modify: `app/services/arabic.py` (дописать в конец файла)
- Modify: `tests/services/test_arabic.py` (дописать в конец файла)

**Interfaces:**
- Consumes: `app.services.arabic.normalize_arabic`.
- Produces: `app.services.arabic.match_words_in_sentence(sentence: str, known: dict[str, int]) -> set[int]`, где `known` — отображение `arabic_norm -> word_id`.

- [ ] **Step 1: Написать падающие тесты**

Дописать в конец `tests/services/test_arabic.py`:

```python
from app.services.arabic import match_words_in_sentence

# arabic_norm -> word_id
KNOWN = {
    "كتاب": 1,
    "بيت": 2,
    "قمر": 3,
    "مدرسة": 4,
    "مدرس": 5,
    "كبير": 6,
}


def test_matches_bare_word() -> None:
    assert match_words_in_sentence("هَذَا بَيْتٌ", KNOWN) == {2}


def test_matches_word_with_definite_article() -> None:
    assert match_words_in_sentence("الْكِتَابُ هُنَا", KNOWN) == {1}


def test_matches_word_with_conjunction_and_article() -> None:
    assert match_words_in_sentence("وَالْقَمَرُ", KNOWN) == {3}


def test_matches_several_words_in_one_sentence() -> None:
    assert match_words_in_sentence("الْمُدَرِّسُ فِي الْمَدْرَسَةِ", KNOWN) == {4, 5}


def test_full_form_wins_over_stripped_prefix() -> None:
    # بيت must match as a whole; it must not be read as ب + يت.
    assert match_words_in_sentence("بَيْت", KNOWN) == {2}


def test_unknown_words_are_ignored() -> None:
    assert match_words_in_sentence("هَذَا شَيْءٌ غَرِيبٌ", KNOWN) == set()


def test_punctuation_does_not_break_matching() -> None:
    assert match_words_in_sentence("هَذَا بَيْتٌ كَبِيرٌ.", KNOWN) == {2, 6}


def test_empty_sentence() -> None:
    assert match_words_in_sentence("", KNOWN) == set()


def test_empty_dictionary() -> None:
    assert match_words_in_sentence("الْكِتَابُ", {}) == set()
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_arabic.py -v`
Expected: FAIL с `ImportError: cannot import name 'match_words_in_sentence'`.

- [ ] **Step 3: Реализовать сопоставление**

Дописать в конец `app/services/arabic.py`:

```python
_ARABIC_LETTERS = re.compile(r"[\u0621-\u064A]+")

_DEFINITE_ARTICLE = "\u0627\u0644"  # al-

# Single-letter proclitics that attach to the following word: wa, fa, bi, li, ka.
_PROCLITICS = ("\u0648", "\u0641", "\u0628", "\u0644", "\u0643")  # wa, fa, bi, li, ka


def _candidate_forms(token: str) -> list[str]:
    """Forms to try for one normalized token, most specific first.

    The full form is tried first on purpose: stripping a leading letter from a
    word that simply starts with it (بيت -> يت) must never win over an exact
    dictionary hit.
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


def match_words_in_sentence(sentence: str, known: dict[str, int]) -> set[int]:
    """Find which dictionary words a sentence uses.

    `known` maps a word's normalized form (Word.arabic_norm) to its id.
    """
    if not known:
        return set()

    matched: set[int] = set()
    for token in _ARABIC_LETTERS.findall(normalize_arabic(sentence)):
        for form in _candidate_forms(token):
            word_id = known.get(form)
            if word_id is not None:
                matched.add(word_id)
                break

    return matched
```

- [ ] **Step 4: Убедиться, что все тесты файла проходят**

Run: `uv run pytest tests/services/test_arabic.py -v`
Expected: PASS, 21 тест (12 из задачи 2 + 9 новых).

- [ ] **Step 5: Закоммитить**

```bash
git add app/services/arabic.py tests/services/test_arabic.py
git commit -m "feat: match sentence tokens to dictionary words through proclitics"
```

**Проверка задачи для владельца:** `uv run pytest tests/services/test_arabic.py -v` — 21 тест зелёный; `وَالْقَمَرُ` находит слово `قمر`, а `بَيْت` не разваливается на `ب` + `يت`.

---

### Task 4: Модели данных и первая миграция

**Files:**
- Create: `app/db/enums.py`, `app/db/models.py`
- Create: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/` (генерируются `alembic init`)
- Modify: `alembic/env.py` (подключить настройки и `Base.metadata`)
- Test: `tests/conftest.py`, `tests/db/test_models.py`

**Interfaces:**
- Consumes: `app.db.base.Base`, `app.config.get_settings`, `app.services.arabic.normalize_arabic`.
- Produces:
  - `app.db.enums.Direction` (`AR_RU = "ar_ru"`, `RU_AR = "ru_ar"`), `app.db.enums.ContentSource` (`TEXTBOOK = "textbook"`, `AI_GENERATED = "ai_generated"`).
  - `app.db.models.User`, `Word`, `Sentence`, `SentenceWord`, `UserProgress`, `ReviewLog`.
  - Фикстура `session` в `tests/conftest.py` — `AsyncSession` на тестовой БД с откатом транзакции после теста.

- [ ] **Step 1: Создать перечисления**

`app/db/enums.py`:

```python
from enum import StrEnum


class Direction(StrEnum):
    """A word yields two independent SRS cards."""

    AR_RU = "ar_ru"
    RU_AR = "ru_ar"


class ContentSource(StrEnum):
    TEXTBOOK = "textbook"
    AI_GENERATED = "ai_generated"
```

- [ ] **Step 2: Создать модели**

`app/db/models.py`:

```python
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    DateTime,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import ContentSource, Direction


def _enum_column(enum_cls: type[StrEnum], length: int) -> SAEnum:
    """VARCHAR column holding an enum's *value*.

    Two non-obvious settings. Without values_callable SQLAlchemy stores the member
    NAME ("TEXTBOOK") instead of the value ("textbook") the spec fixes. With
    native_enum=True it would create a Postgres ENUM type, which turns every future
    value into a migration; a plain VARCHAR keeps that cheap.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        create_constraint=False,
        values_callable=lambda members: [member.value for member in members],
    )


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(Text)
    first_name: Mapped[str | None] = mapped_column(Text)
    # Daily cap on new cards, per user.
    new_per_day: Mapped[int] = mapped_column(default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Word(Base):
    __tablename__ = "words"
    __table_args__ = (
        UniqueConstraint("arabic_norm", "translation_ru", name="uq_words_norm_translation"),
        Index("ix_words_arabic_norm", "arabic_norm"),
        Index("ix_words_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stored exactly as recognised, WITH diacritics.
    arabic: Mapped[str] = mapped_column(Text)
    # Comparison key, see services.arabic.normalize_arabic.
    arabic_norm: Mapped[str] = mapped_column(Text)
    translation_ru: Mapped[str] = mapped_column(Text)
    transliteration: Mapped[str | None] = mapped_column(Text)
    # Free-form label, replaces the lesson entity: "еда", "глаголы движения".
    topic: Mapped[str | None] = mapped_column(Text)
    source: Mapped[ContentSource] = mapped_column(_enum_column(ContentSource, 16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sentence_links: Mapped[list["SentenceWord"]] = relationship(
        back_populates="word", cascade="all, delete-orphan"
    )


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    arabic: Mapped[str] = mapped_column(Text)
    translation_ru: Mapped[str] = mapped_column(Text)
    source: Mapped[ContentSource] = mapped_column(_enum_column(ContentSource, 16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    word_links: Mapped[list["SentenceWord"]] = relationship(
        back_populates="sentence", cascade="all, delete-orphan"
    )


class SentenceWord(Base):
    """Link table. Powers example sentences on the card back and per-user novelty."""

    __tablename__ = "sentence_words"

    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), primary_key=True
    )
    word_id: Mapped[int] = mapped_column(
        ForeignKey("words.id", ondelete="CASCADE"), primary_key=True
    )

    sentence: Mapped[Sentence] = relationship(back_populates="word_links")
    word: Mapped[Word] = relationship(back_populates="sentence_links")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint(
            "telegram_id", "word_id", "direction", name="uq_progress_user_word_direction"
        ),
        Index("ix_user_progress_due", "telegram_id", "due"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"))
    direction: Mapped[Direction] = mapped_column(_enum_column(Direction, 8))
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Serialised FSRS card; the scheduler runs server-side.
    fsrs_state: Mapped[dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ReviewLog(Base):
    """Rating history. Needed later to fit FSRS parameters for this group.

    No FK on telegram_id on purpose: history outlives a deleted user.
    """

    __tablename__ = "review_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"))
    direction: Mapped[Direction] = mapped_column(_enum_column(Direction, 8))
    # FSRS rating scale: 1 again, 2 hard, 3 good, 4 easy.
    rating: Mapped[int] = mapped_column(SmallInteger)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 3: Инициализировать Alembic**

Run: `uv run alembic init -t async alembic`
Expected: созданы `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/`.

- [ ] **Step 4: Подключить Alembic к настройкам и моделям**

`alembic init -t async` генерирует рабочий `env.py` — его надо не переписывать, а
дополнить в трёх местах. Сгенерированный файл уже содержит `import asyncio` и
`asyncio.run(...)`; удалить их нельзя, иначе миграции перестанут запускаться.

**6.1.** Добавить импорты после уже существующих:

```python
from app.config import get_settings
from app.db import models  # noqa: F401  # registers all mappers on Base.metadata
from app.db.base import Base
```

**6.2.** Заменить строку `target_metadata = None` на две:

```python
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata
```

**6.3.** В обоих вызовах `context.configure(...)` (в `run_migrations_offline` и в
`do_run_migrations`) добавить аргумент:

```python
        compare_type=True,
```

**6.4.** В `alembic.ini` удалить строку `sqlalchemy.url = ...` — URL приходит из
настроек, и оставленная в ini пустая заглушка перекроет его.

- [ ] **Step 5: Сгенерировать и применить миграцию**

Run: `uv run alembic revision --autogenerate -m "initial schema"`
Expected: создан файл в `alembic/versions/` с `op.create_table` для шести таблиц.

Run: `uv run alembic upgrade head`
Expected: `Running upgrade -> <rev>, initial schema` без ошибок.

Run: `docker compose exec db psql -U mufradat -d mufradat -c '\dt'`
Expected: в списке `users`, `words`, `sentences`, `sentence_words`, `user_progress`, `review_log`, `alembic_version`.

- [ ] **Step 6: Написать фикстуры тестовой БД**

`tests/conftest.py`:

```python
from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db import models  # noqa: F401  # registers mappers before create_all
from app.db.base import Base


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    """Engine bound to the dedicated test database, with a freshly built schema."""
    engine = create_async_engine(get_settings().test_database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Session inside a transaction that is rolled back, so tests stay isolated."""
    connection = await engine.connect()
    transaction = await connection.begin()
    maker = async_sessionmaker(bind=connection, expire_on_commit=False)
    async with maker() as session:
        yield session
    await transaction.rollback()
    await connection.close()
```

- [ ] **Step 7: Написать тесты моделей**

`tests/db/test_models.py`:

```python
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ContentSource, Direction
from app.db.models import Sentence, SentenceWord, Word
from app.services.arabic import normalize_arabic


def make_word(arabic: str, translation: str) -> Word:
    return Word(
        arabic=arabic,
        arabic_norm=normalize_arabic(arabic),
        translation_ru=translation,
        source=ContentSource.TEXTBOOK,
    )


async def test_word_round_trips_with_diacritics(session: AsyncSession) -> None:
    session.add(make_word("كِتَاب", "книга"))
    await session.flush()

    stored = (await session.execute(select(Word))).scalar_one()
    assert stored.arabic == "كِتَاب"
    assert stored.arabic_norm == "كتاب"
    assert stored.source is ContentSource.TEXTBOOK
    assert stored.created_at is not None


async def test_same_word_with_different_harakat_is_rejected(session: AsyncSession) -> None:
    session.add(make_word("مُدَرِّس", "учитель"))
    await session.flush()

    # Same skeleton, different diacritics — must collide on (arabic_norm, translation_ru).
    session.add(make_word("مُدَرِّسٌ", "учитель"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_same_skeleton_with_different_translation_is_allowed(session: AsyncSession) -> None:
    session.add(make_word("عَيْن", "глаз"))
    session.add(make_word("عَيْن", "источник"))
    await session.flush()

    words = (await session.execute(select(Word))).scalars().all()
    assert len(words) == 2


async def test_sentence_links_to_words(session: AsyncSession) -> None:
    word = make_word("بَيْت", "дом")
    sentence = Sentence(
        arabic="هَذَا بَيْتٌ كَبِيرٌ",
        translation_ru="Это большой дом.",
        source=ContentSource.TEXTBOOK,
    )
    session.add_all([word, sentence])
    await session.flush()

    session.add(SentenceWord(sentence_id=sentence.id, word_id=word.id))
    await session.flush()

    link = (await session.execute(select(SentenceWord))).scalar_one()
    assert link.sentence_id == sentence.id
    assert link.word_id == word.id


async def test_source_stored_as_value_not_member_name(session: AsyncSession) -> None:
    # Guards the values_callable setting in _enum_column: without it the column
    # would hold "TEXTBOOK" and every consumer of the raw value would break.
    session.add(make_word("بَاب", "дверь"))
    await session.flush()

    raw = (await session.execute(text("select source from words"))).scalar_one()
    assert raw == "textbook"


async def test_direction_enum_values() -> None:
    assert Direction.AR_RU == "ar_ru"
    assert Direction.RU_AR == "ru_ar"
```

- [ ] **Step 8: Прогнать тесты**

Run: `uv run pytest tests -v`
Expected: PASS, все тесты (7 конфигурация + 21 арабский + 6 модели).

- [ ] **Step 9: Проверить, что миграция и модели не расходятся**

Run: `uv run alembic revision --autogenerate -m "should be empty"`
Expected: в созданном файле `upgrade()` пустой (только `pass`). Если появились операции — модели и миграция расходятся, поправить и перегенерировать.

Run: `rm alembic/versions/*should_be_empty*.py`
Expected: файл-проверка удалён.

- [ ] **Step 10: Закоммитить**

```bash
git add app/db/ alembic.ini alembic/ tests/
git commit -m "feat: data model with normalized Arabic column and initial migration"
```

**Проверка задачи для владельца:** `\dt` показывает шесть таблиц; попытка вставить то же слово с другими огласовками падает на уникальном ограничении; повторный autogenerate пустой.

---

### Task 5: Сервис дедупликации

Отвечает на вопрос, который бот задаёт при импорте каждой распознанной пары: это новое слово, точный дубль или похожее слово с другим переводом.

**Files:**
- Create: `app/services/dedup.py`
- Test: `tests/services/test_dedup.py`

**Interfaces:**
- Consumes: `app.db.models.Word`, `app.services.arabic.normalize_arabic`, фикстура `session`.
- Produces:
  - `app.services.dedup.DuplicateKind` (`NONE = "none"`, `EXACT = "exact"`, `SIMILAR = "similar"`).
  - `app.services.dedup.DuplicateCheck` — frozen dataclass с полями `kind: DuplicateKind`, `existing_word_id: int | None`, `existing_translation: str | None`.
  - `app.services.dedup.check_duplicate(session: AsyncSession, arabic: str, translation_ru: str) -> DuplicateCheck`.

- [ ] **Step 1: Написать падающие тесты**

`tests/services/test_dedup.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ContentSource
from app.db.models import Word
from app.services.arabic import normalize_arabic
from app.services.dedup import DuplicateKind, check_duplicate


async def add_word(session: AsyncSession, arabic: str, translation: str) -> Word:
    word = Word(
        arabic=arabic,
        arabic_norm=normalize_arabic(arabic),
        translation_ru=translation,
        source=ContentSource.TEXTBOOK,
    )
    session.add(word)
    await session.flush()
    return word


async def test_unknown_word_is_new(session: AsyncSession) -> None:
    result = await check_duplicate(session, "كِتَاب", "книга")

    assert result.kind is DuplicateKind.NONE
    assert result.existing_word_id is None


async def test_identical_word_is_exact_duplicate(session: AsyncSession) -> None:
    word = await add_word(session, "كِتَاب", "книга")

    result = await check_duplicate(session, "كِتَاب", "книга")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_word_id == word.id


async def test_different_harakat_still_counts_as_exact(session: AsyncSession) -> None:
    word = await add_word(session, "مُدَرِّس", "учитель")

    result = await check_duplicate(session, "مُدَرِّسٌ", "учитель")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_word_id == word.id


async def test_translation_comparison_ignores_case_and_spaces(session: AsyncSession) -> None:
    word = await add_word(session, "بَيْت", "дом")

    result = await check_duplicate(session, "بَيْت", "  Дом ")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_word_id == word.id


async def test_same_skeleton_other_translation_is_similar(session: AsyncSession) -> None:
    word = await add_word(session, "عَيْن", "глаз")

    result = await check_duplicate(session, "عَيْن", "источник")

    assert result.kind is DuplicateKind.SIMILAR
    assert result.existing_word_id == word.id
    assert result.existing_translation == "глаз"


async def test_exact_match_wins_over_similar(session: AsyncSession) -> None:
    await add_word(session, "عَيْن", "глаз")
    expected = await add_word(session, "عَيْن", "источник")

    result = await check_duplicate(session, "عَيْن", "источник")

    assert result.kind is DuplicateKind.EXACT
    assert result.existing_word_id == expected.id
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `uv run pytest tests/services/test_dedup.py -v`
Expected: FAIL с `ModuleNotFoundError: No module named 'app.services.dedup'`.

- [ ] **Step 3: Реализовать сервис**

`app/services/dedup.py`:

```python
"""Duplicate detection for imported words."""

from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Word
from app.services.arabic import normalize_arabic


class DuplicateKind(StrEnum):
    NONE = "none"
    EXACT = "exact"
    # Same skeleton, different translation: possibly a homograph, so the admin decides.
    SIMILAR = "similar"


@dataclass(frozen=True)
class DuplicateCheck:
    kind: DuplicateKind
    existing_word_id: int | None = None
    existing_translation: str | None = None


def _same_translation(left: str, right: str) -> bool:
    return left.strip().casefold() == right.strip().casefold()


async def check_duplicate(
    session: AsyncSession, arabic: str, translation_ru: str
) -> DuplicateCheck:
    """Classify an incoming (arabic, translation) pair against the shared deck."""
    norm = normalize_arabic(arabic)
    candidates = (
        (await session.execute(select(Word).where(Word.arabic_norm == norm))).scalars().all()
    )

    if not candidates:
        return DuplicateCheck(DuplicateKind.NONE)

    for candidate in candidates:
        if _same_translation(candidate.translation_ru, translation_ru):
            return DuplicateCheck(
                DuplicateKind.EXACT, candidate.id, candidate.translation_ru
            )

    first = candidates[0]
    return DuplicateCheck(DuplicateKind.SIMILAR, first.id, first.translation_ru)
```

- [ ] **Step 4: Прогнать тесты**

Run: `uv run pytest tests/services/test_dedup.py -v`
Expected: PASS, 6 тестов.

- [ ] **Step 5: Закоммитить**

```bash
git add app/services/dedup.py tests/services/test_dedup.py
git commit -m "feat: classify imported words as new, exact duplicate or similar"
```

**Проверка задачи для владельца:** слово с другими огласовками распознаётся как точный дубль; то же слово с другим переводом — как «похожее», а не как дубль.

---

### Task 6: Сидер и README

**Files:**
- Create: `scripts/seed.py`
- Create: `README.md`
- Test: проверяется запуском сидера и SQL-запросом (данные, не логика).

**Interfaces:**
- Consumes: `app.db.session.get_sessionmaker`, `app.db.models`, `app.services.arabic.normalize_arabic`, `match_words_in_sentence`.
- Produces: `scripts/seed.py` как исполняемый скрипт (`uv run python scripts/seed.py`), идемпотентный.

- [ ] **Step 1: Написать сидер**

`scripts/seed.py`:

```python
"""Seed the shared deck with a small textbook-like sample.

Idempotent: re-running it does not duplicate rows.
"""

import asyncio

from sqlalchemy import select

from app.db.enums import ContentSource
from app.db.models import Sentence, SentenceWord, Word
from app.db.session import get_engine, get_sessionmaker
from app.services.arabic import match_words_in_sentence, normalize_arabic

# (arabic with harakat, russian, transliteration, topic)
WORDS: list[tuple[str, str, str, str]] = [
    ("بَيْت", "дом", "bayt", "быт"),
    ("كِتَاب", "книга", "kitab", "учёба"),
    ("مَدْرَسَة", "школа", "madrasa", "учёба"),
    ("مُدَرِّس", "учитель", "mudarris", "учёба"),
    ("طَالِب", "студент", "talib", "учёба"),
    ("قَلَم", "ручка", "qalam", "учёба"),
    ("مَاء", "вода", "ma'", "еда"),
    ("خُبْز", "хлеб", "khubz", "еда"),
    ("بَاب", "дверь", "bab", "быт"),
    ("وَلَد", "мальчик", "walad", "люди"),
    ("بِنْت", "девочка", "bint", "люди"),
    ("رَجُل", "мужчина", "rajul", "люди"),
    ("اِمْرَأَة", "женщина", "imra'a", "люди"),
    ("صَدِيق", "друг", "sadiq", "люди"),
    ("مَدِينَة", "город", "madina", "город"),
    ("سَيَّارَة", "машина", "sayyara", "город"),
    ("شَمْس", "солнце", "shams", "природа"),
    ("قَمَر", "луна", "qamar", "природа"),
    ("يَوْم", "день", "yawm", "время"),
    ("كَبِير", "большой", "kabir", "признаки"),
]

# (arabic with harakat, russian)
SENTENCES: list[tuple[str, str]] = [
    ("هَذَا بَيْتٌ كَبِيرٌ", "Это большой дом."),
    ("الْمُدَرِّسُ فِي الْمَدْرَسَةِ", "Учитель в школе."),
    ("الْوَلَدُ يَشْرَبُ الْمَاءَ", "Мальчик пьёт воду."),
    ("هَذَا قَلَمُ الطَّالِبِ", "Это ручка студента."),
    ("الشَّمْسُ وَالْقَمَرُ", "Солнце и луна."),
]


async def main() -> None:
    maker = get_sessionmaker()
    async with maker() as session:
        existing_words = {
            word.arabic_norm: word.id
            for word in (await session.execute(select(Word))).scalars().all()
        }

        added_words = 0
        for arabic, translation, transliteration, topic in WORDS:
            norm = normalize_arabic(arabic)
            if norm in existing_words:
                continue
            word = Word(
                arabic=arabic,
                arabic_norm=norm,
                translation_ru=translation,
                transliteration=transliteration,
                topic=topic,
                source=ContentSource.TEXTBOOK,
            )
            session.add(word)
            await session.flush()
            existing_words[norm] = word.id
            added_words += 1

        existing_sentences = {
            sentence.arabic
            for sentence in (await session.execute(select(Sentence))).scalars().all()
        }

        added_sentences = 0
        added_links = 0
        for arabic, translation in SENTENCES:
            if arabic in existing_sentences:
                continue
            sentence = Sentence(
                arabic=arabic,
                translation_ru=translation,
                source=ContentSource.TEXTBOOK,
            )
            session.add(sentence)
            await session.flush()
            added_sentences += 1

            for word_id in match_words_in_sentence(arabic, existing_words):
                session.add(SentenceWord(sentence_id=sentence.id, word_id=word_id))
                added_links += 1

        await session.commit()

    print(f"words +{added_words}, sentences +{added_sentences}, links +{added_links}")
    await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Запустить сидер**

Run: `uv run python scripts/seed.py`
Expected: ровно `words +20, sentences +5, links +10` — по два связанных слова
в каждом из пяти предложений.

- [ ] **Step 3: Проверить идемпотентность**

Run: `uv run python scripts/seed.py`
Expected: `words +0, sentences +0, links +0`.

- [ ] **Step 4: Проверить связки в БД**

Run:
```bash
docker compose exec db psql -U mufradat -d mufradat -c \
  "select s.translation_ru, count(sw.word_id) as words
   from sentences s left join sentence_words sw on sw.sentence_id = s.id
   group by s.id, s.translation_ru order by s.id;"
```
Expected: у каждого из пяти предложений минимум одно связанное слово; у «Учитель в школе.» — два, у «Солнце и луна.» — два.

- [ ] **Step 5: Написать README**

`README.md`:

````markdown
# Mufradat Bot

Telegram Mini App для заучивания арабских слов группой из ~10 человек. Общая
колода на всех: админ наполняет базу через фото страниц учебника, остальные учат
по карточкам с интервальным повторением (FSRS). Личный прогресс — у каждого свой.

Дизайн: `docs/superpowers/specs/2026-08-05-mufradat-bot-design.md`.

## Требования

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker (для Postgres 16)

## Локальный запуск

```bash
cp .env.example .env         # порт 5433, чтобы не конфликтовать с локальным Postgres
docker compose up -d         # Postgres 16 + отдельная тестовая база
uv sync --extra dev
uv run alembic upgrade head
uv run python scripts/seed.py
```

Проверка соединения: `uv run python scripts/check_db.py`.

## Тесты

```bash
uv run pytest            # весь набор
uv run ruff check .      # линтер
```

Тесты, которым нужна БД, идут в отдельную базу `mufradat_test` (создаётся
автоматически при первом старте контейнера) и откатывают транзакцию после
каждого теста.

## Структура

| Путь | Ответственность |
|---|---|
| `app/config.py` | настройки из `.env`, гейтинг админа |
| `app/db/` | модели SQLAlchemy, сессии, перечисления |
| `app/services/arabic.py` | нормализация арабского, сопоставление слов предложения |
| `app/services/dedup.py` | классификация импортируемых слов |
| `alembic/` | миграции |
| `scripts/` | проверка соединения, сидер |
````

- [ ] **Step 6: Прогнать весь набор тестов и линтер**

Run: `uv run pytest -v && uv run ruff check . && uv run ruff format --check .`
Expected: все тесты PASS, линтер без ошибок.

- [ ] **Step 7: Закоммитить**

```bash
git add scripts/seed.py README.md
git commit -m "feat: idempotent seeder with sample vocabulary and README"
```

**Проверка задачи для владельца:** сидер заливает 20 слов и 5 предложений со связками, повторный запуск ничего не добавляет, README описывает запуск с нуля.

---

## Что дальше

Следующие планы (пишутся по одному, после одобрения предыдущего):

| План | Содержание | Этап спеки |
|---|---|---|
| 2 | Скелет бота: `/start` печатает Telegram ID, роли, `/help` | 3 |
| 3 | Импорт по фото: vision, FSM подтверждения, запись | 4 |
| 4 | FastAPI: валидация `initData`, очереди, FSRS | 5 |
| 5 | Mini App на Vue 3: три режима, карточки | 6 |
| 6 | Генерация предложений и кандидаты в новые слова | 7 |
| 7 | Полировка: счётчики, фильтры, лимиты, обработка ошибок | 8 |
