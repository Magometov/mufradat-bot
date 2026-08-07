import csv
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.vocabulary.management.commands import generate_images
from apps.vocabulary.models import Entry
from apps.vocabulary.pictures import PROMPTS, STYLE

pytestmark = pytest.mark.django_db

#: Выгрузка колоды с сервера. В репозиторий не едет, без неё проверки по ней пропускаются.
SNAPSHOT = Path(__file__).resolve().parents[3] / "docs" / "superpowers" / "words.csv"

needs_snapshot = pytest.mark.skipif(not SNAPSHOT.exists(), reason=f"нет выгрузки: {SNAPSHOT}")

JPEG = b"\xff\xd8\xff\xe0 fake jpeg"


@pytest.fixture(autouse=True)
def media(settings, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def key(monkeypatch) -> None:
    monkeypatch.setenv("FAL_KEY", "test-key")


@pytest.fixture
def calls(monkeypatch) -> list[str]:
    """Подменяет сеть: собирает промпты, с которыми позвали модель."""
    seen: list[str] = []

    def fake_generate(prompt: str, api_key: str) -> str:
        seen.append(prompt)
        return "https://example.test/picture.jpg"

    monkeypatch.setattr(generate_images, "generate", fake_generate)
    monkeypatch.setattr(generate_images, "download", lambda url: JPEG)

    return seen


def run(*args: str) -> str:
    out = StringIO()
    call_command("generate_images", *args, stdout=out)
    return out.getvalue()


def test_without_key_command_says_so(monkeypatch) -> None:
    monkeypatch.delenv("FAL_KEY", raising=False)
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    with pytest.raises(CommandError, match="FAL_KEY"):
        run()


def test_dry_run_needs_no_key(monkeypatch) -> None:
    """Промпты надо уметь просмотреть до того, как заводить ключ и платить."""
    monkeypatch.delenv("FAL_KEY", raising=False)
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    assert "верблюд" in run("--dry-run")


def test_picture_is_saved(key, calls) -> None:
    entry = Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    run()

    entry.refresh_from_db()
    assert entry.image.name.endswith(f"{entry.pk}.jpg")
    assert entry.image.read() == JPEG


def test_style_is_appended_to_every_prompt(key, calls) -> None:
    """Без общей приписки колода выглядит свалкой: у каждой картинки свой фон и манера."""
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    run()

    assert calls == [f"{PROMPTS['верблюд']}, {STYLE}"]


def test_words_outside_the_dictionary_are_left_alone(key, calls) -> None:
    """Словарь и есть белый список: «гражданство» нарисовать нечем."""
    Entry.objects.create(arabic="جِنْسِيَّة", translation_ru="национальность, гражданство")

    run()

    assert calls == []


def test_already_drawn_cards_are_skipped(key, calls) -> None:
    """Пропуск делает прогон возобновляемым: его можно прервать и добрать остаток."""
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    run()

    assert run().count("верблюд") == 0


def test_replace_draws_again(key, calls) -> None:
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    run()

    run("--replace")

    assert len(calls) == 2


def test_only_takes_the_named_cards(key, calls) -> None:
    camel = Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    Entry.objects.create(arabic="كِتَاب", translation_ru="книга")

    run("--only", str(camel.pk))

    assert calls == [f"{PROMPTS['верблюд']}, {STYLE}"]


def test_limit_stops_early(key, calls) -> None:
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    Entry.objects.create(arabic="كِتَاب", translation_ru="книга")

    run("--limit", "1")

    assert len(calls) == 1


def test_one_broken_card_does_not_stop_the_run(key, calls, monkeypatch) -> None:
    """Прогон идёт сотнями карточек — падать целиком из-за одной он не должен."""

    def flaky(prompt: str, api_key: str) -> str:
        if "camel" in prompt:
            raise ValueError("модель не вернула картинку")
        return "https://example.test/picture.jpg"

    monkeypatch.setattr(generate_images, "generate", flaky)
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    book = Entry.objects.create(arabic="كِتَاب", translation_ru="книга")

    output = run()

    book.refresh_from_db()
    assert bool(book.image)
    assert "Сорвалось: 1" in output


@pytest.fixture(scope="module")
def snapshot() -> list[dict[str, str]]:
    with SNAPSHOT.open(encoding="utf-8") as file:
        return list(csv.DictReader(file))


@needs_snapshot
def test_every_prompt_matches_a_real_card(snapshot: list[dict[str, str]]) -> None:
    """Опечатка в ключе оставила бы карточку без картинки молча."""
    translations = {row["translation_ru"] for row in snapshot}

    assert sorted(key for key in PROMPTS if key not in translations) == []


@needs_snapshot
def test_first_batch_is_two_hundred_cards(snapshot: list[dict[str, str]]) -> None:
    """Ровно 200: столько владелец согласился рисовать в первую партию."""
    covered = [row for row in snapshot if row["translation_ru"] in PROMPTS]

    assert len(covered) == 200
