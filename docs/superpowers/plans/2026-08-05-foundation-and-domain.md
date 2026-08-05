# Mufradat Bot — план 1: каркас и домен (Django)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Поднять Django-проект с рабочей БД, схемой данных, админкой, протестированной логикой обработки арабского и редактируемым файлом поведения ИИ — фундамент, на который встанут бот, API и Mini App.

**Architecture:** Питон живёт в `backend/`: `config/` (настройки, urls, wsgi) и приложение `apps/vocabulary/` (модели, админка, домен). Настройки читаются через `os.getenv` + `python-dotenv`, те же переменные читает `docker-compose.yml`, поэтому параметры БД не дублируются. Логика обработки арабского живёт в `backend/apps/vocabulary/services/arabic.py` как чистые функции без БД и тестируется полностью; всё, что требует БД, тестируется на реальном Postgres 16 через `pytest-django`, который сам создаёт и удаляет тестовую базу.

**Tech Stack:** Python 3.12, Django 6.0, psycopg 3.3, Postgres 16 в Docker, python-dotenv, pydantic, PyYAML, Pillow, pytest + pytest-django, uv.

Покрывает этапы 1–2 спеки `docs/superpowers/specs/2026-08-05-mufradat-bot-design.md` (ревизия 3).

## Global Constraints

- Python 3.12 (`requires-python = ">=3.12,<3.13"`). Зависимости — через `uv sync`.
- Идентификаторы — на английском. **Docstring и построчные комментарии — на русском
  и коротко**; комментарий пишется только там, где объясняет решение, а не
  пересказывает код (решения владельца по ходу задачи 1). В блоках кода ниже часть
  комментариев осталась на английском — при реализации переводятся. Всё, что видит пользователь
  (админка, данные сидера) — на русском.
- Локальный Postgres 14 не трогаем: контейнер слушает **порт 5433**.
- Никаких секретов в коде. `.env` в `.gitignore`; `.env.example` — только имена и
  комментарии, без значений.
- Версии (проверены на PyPI 2026-08-05): `django>=6.0,<6.1`,
  `psycopg[binary]>=3.3,<3.4`, `python-dotenv>=1.2,<2`, `pydantic>=2.13,<3`, `pillow>=12.3,<13`,
  `pyyaml>=6,<7`, `pytest>=9.1,<10`, `pytest-django>=4.12,<5`, `ruff>=0.16,<0.17`.
  DRF, aiogram, fsrs и anthropic добавляются в своих планах, не здесь.
- Django 6: у `CheckConstraint` аргумент называется `condition`, а не `check`
  (`check` удалён в 6.0).
- `USE_TZ = True`, все временные метки — `TIMESTAMPTZ`.
- Арабский в тестах и сидере — реальный, с огласовками.
- Каждая задача заканчивается коммитом, затем остановка и одобрение владельца.

---

### Task 1: Каркас Django, конфигурация, БД — **выполнено**

Структуру по ходу работы задал владелец, поэтому здесь записано фактическое
состояние, а не исходные шаги.

```
docker-compose.yml  pyproject.toml  .env  .env.example      # корень
backend/manage.py
backend/config/{settings,urls,wsgi}.py
backend/apps/vocabulary/{apps.py,migrations/}
backend/tests/
```

- Настройки — `os.getenv` плюс `python-dotenv`; `.env` читается из корня репозитория,
  и уже заданные переменные окружения не перезаписываются, поэтому в Docker побеждает
  реальное окружение.
- Параметры БД (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_NAME`, `POSTGRES_HOST`,
  `POSTGRES_PORT`) читают и `docker-compose.yml`, и Django — значения только в `.env`.
- `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` задан глобально: иначе модели
  из задачи 4 дадут предупреждения `models.W042`.
- `verbose_name` приложения — «Словарный запас», это заголовок раздела в админке.
- Тестов на `settings` нет по решению владельца: конфигурация проверяется тем, что
  проект поднимается.

Проверка: `uv run python backend/manage.py check` без замечаний, `migrate` проходит,
админка отдаёт HTTP 200.

---

### Задачи 2 и 3 — сделаны и **отменены**

`normalize_arabic` и `match_entries_in_sentence` были написаны и покрыты 21 тестом,
а затем удалены по решению владельца вместе с колонкой `arabic_norm`.

Причина: обе появились ради распознавания страниц учебника — модель могла вернуть то
же слово с иной расстановкой харакат, и сравнение по скелету ловило такой дубль.
Распознавания больше нет, слова вводятся руками, и от повторов достаточно ограничения
в БД на точную пару «арабское + перевод».

Код восстанавливается из коммита `171860f`, если понадобится на этапе 7: генерация
предложений захочет знать, какие слова в них использованы.

---

### Task 4: Модель Entry и первая миграция — **выполнено**

По ходу задачи владелец сократил объём: всё, чем не пользуются задачи 5–8, перенесено
на свои этапы (см. таблицу «Схема строится по частям» в спеке).

Что сделано:

- `backend/apps/vocabulary/enums.py` — `Kind` (слово, фраза) и `Source`.
- `backend/apps/vocabulary/models/` — пакет, а не один файл; сейчас в нём `entry.py`.
- `Entry`: восемь полей и одно ограничение `unique(arabic, translation_ru)` — по
  **точному** арабскому, потому что пара «к мужчине / к женщине» различается только
  последней харакой (§4.1 спеки). `arabic_norm` заполняется в `save()`.
- У всех полей `verbose_name` на русском, у моделей — `verbose_name`/`verbose_name_plural`.
- Миграция `0001_initial`, применена; `makemigrations --check` пустой.
- `backend/tests/db/test_entry.py` — 4 теста, включая регрессию на пару м/ж.
- В `pyproject.toml` добавлен `src = ["backend"]`, иначе ruff считает `apps` и `config`
  сторонними пакетами и неверно сортирует импорты.

Проверка: `uv run pytest` — 25 passed, `ruff check` чист, в БД одна таблица
`vocabulary_entry`.

---

### Task 5: Картинка у единицы и админка — **выполнено**

- `Entry.image` — `ImageField`, картинки загружаются вручную через админку;
  автоподбор из Openverse отменён вместе с фото-импортом.
- Из модели убраны `arabic_norm` и `source`: первое — вместе с нормализацией, второе
  потому что до этапа 7 у всех записей было бы одно значение.
- `EntryAdmin`: список с фильтром по типу, поиск по переводу и транслитерации
  (арабский в поиске не нужен — владелец ищет по-русски), картинка отдельным блоком.
- Поле `topic` тоже убрано: деления на темы у группы нет, колода плоская. Фильтр в
  «Тренировке» остаётся по `created_at` — «последние N добавленных».
- `backend/tests/db/test_admin.py` — 4 теста: список открывается, форма добавления
  открывается, слово реально сохраняется через POST, поиск по-русски находит нужное.

Проверка: `uv run pytest` — 7 passed, `manage.py check` без замечаний.

---

### Task 6: Файл поведения ИИ и его загрузчик

**Files:**
- Create: `backend/content/curriculum.yaml`
- Create: `backend/apps/vocabulary/services/curriculum.py`
- Test: `backend/tests/services/test_curriculum.py`

**Interfaces:**
- Consumes: `vocabulary.enums.Person`.
- Produces:
  - Список допустимых местоимений в загрузчике — константа: перечисление `Person` появится вместе с формами на этапе 9.
  - `apps.vocabulary.services.curriculum.Curriculum` — `rules: Rules`, `topics: list[Topic]`; методы `enabled_topics() -> list[Topic]`, `topic(topic_id: str) -> Topic`.
  - `Rules` — `language_register: str` (в YAML ключ `register`), `harakat: str`, `max_new_words_per_sentence: int`, `forms_per_entry: int`, `pronouns: list[str]`, `service_words: list[str]`.
  - `Topic` — `id`, `title`, `enabled`, `target_count`, `ask_for: list[str]`, `examples: list[Example]`; `Example` — `ar: str`, `ru: str`.
  - `load_curriculum(path: Path | None = None) -> Curriculum`.

- [ ] **Step 1: Создать файл содержания**

`backend/backend/content/curriculum.yaml`:

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

`backend/tests/services/test_curriculum.py`:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from apps.vocabulary.services.curriculum import load_curriculum

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

Run: `uv run pytest backend/tests/services/test_curriculum.py -q 2>&1 | tail -5`
Expected: FAIL — `ModuleNotFoundError: No module named 'vocabulary.services.curriculum'`.

- [ ] **Step 4: Реализовать загрузчик**

`backend/apps/vocabulary/services/curriculum.py`:

```python
"""Загрузчик `backend/content/curriculum.yaml` — редактируемого описания поведения ИИ.

Проверяется через pydantic, поэтому опечатка в файле даёт внятную ошибку, а не
странный промпт.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from django.conf import settings
from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.vocabulary.enums import Person

DEFAULT_PATH = Path(settings.BASE_DIR) / "content" / "curriculum.yaml"

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

Run: `uv run pytest backend/tests/services/test_curriculum.py -q 2>&1 | tail -3`
Expected: 9 passed.

- [ ] **Step 6: Закоммитить**

```bash
git add backend/content backend/apps/vocabulary/services/curriculum.py tests/services/test_curriculum.py
git commit -m "feat: validated curriculum file driving AI content generation"
```

**Проверка задачи для владельца:** впиши в `backend/content/curriculum.yaml` опечатку в имени поля или несуществующее местоимение — `uv run pytest backend/tests/services/test_curriculum.py::test_shipped_file_is_valid` упадёт с внятным сообщением.

---

### Task 7: Сидер и README

**Files:**
- Create: `backend/apps/vocabulary/management/__init__.py`, `backend/apps/vocabulary/management/commands/__init__.py`, `backend/apps/vocabulary/management/commands/seed_deck.py`
- Create: `README.md`

**Interfaces:**
- Consumes: модели, `match_entries_in_sentence`.
- Produces: команда `uv run python backend/manage.py seed_deck` — идемпотентная.

- [ ] **Step 1: Написать команду**

Создать `backend/apps/vocabulary/management/__init__.py` и `backend/apps/vocabulary/management/commands/__init__.py` пустыми.

`backend/apps/vocabulary/management/commands/seed_deck.py`:

```python
"""Наполнить общую колоду небольшим учебным набором.

Идемпотентно: повторный запуск ничего не добавляет. Есть все три типа единиц,
чтобы очередям было с чем работать.
"""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.vocabulary.enums import Kind, Person, Pos, Source, Tense
from apps.vocabulary.models import Entry, Sentence, SentenceEntry
from apps.vocabulary.services.arabic import match_entries_in_sentence

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

Run: `uv run python backend/manage.py seed_deck`
Expected: ровно `words +21, forms +6, phrases +5, sentences +5, links +10` (числа посчитаны прогоном логики сопоставления на этих данных).

- [ ] **Step 3: Проверить идемпотентность**

Run: `uv run python backend/manage.py seed_deck`
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
uv run python backend/manage.py migrate
uv run python backend/manage.py seed_deck
uv run python backend/manage.py createsuperuser
uv run python backend/manage.py runserver
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
| `backend/config/settings.py` | настройки Django, читает `.env` из корня |
| `backend/apps/vocabulary/models.py` | `Entry` (слова, фразы, формы), примеры, прогресс, история |
| `backend/apps/vocabulary/admin.py` | админка для правки базы без кода |
| `backend/apps/vocabulary/services/arabic.py` | нормализация, сопоставление слов предложения |
| `backend/apps/vocabulary/services/dedup.py` | поиск похожих записей при импорте |
| `backend/apps/vocabulary/services/curriculum.py` | загрузчик `backend/content/curriculum.yaml` |
| `backend/content/curriculum.yaml` | **поведение ИИ: темы, правила, примеры** |

## Как менять поведение ИИ

Правится `backend/content/curriculum.yaml`, код не трогается. Главный рычаг — блок
`examples` внутри темы: модель ловит стиль по образцам точнее, чем по описанию.
Список `pronouns` управляет и формами слов, и лицами во фразах.

Проверить файл после правки:

```bash
uv run pytest backend/tests/services/test_curriculum.py -q
```
````

- [ ] **Step 6: Прогнать весь набор и линтер**

Run: `uv run pytest -q 2>&1 | tail -3 && uv run ruff format . && uv run ruff check .`
Expected: 51 passed, линтер без ошибок.

- [ ] **Step 7: Закоммитить**

```bash
git add backend/apps/vocabulary/management README.md
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
