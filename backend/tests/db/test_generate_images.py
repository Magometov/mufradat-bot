import base64
import csv
import re
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.vocabulary.management.commands import generate_images
from apps.vocabulary.models import Entry
from apps.vocabulary.pictures import _REST, _WITH_WOMEN, MODESTY, PROMPTS, STYLE

pytestmark = pytest.mark.django_db

#: Выгрузка колоды с сервера. В репозиторий не едет, без неё проверки по ней пропускаются.
SNAPSHOT = Path(__file__).resolve().parents[3] / "docs" / "superpowers" / "words.csv"

needs_snapshot = pytest.mark.skipif(not SNAPSHOT.exists(), reason=f"нет выгрузки: {SNAPSHOT}")

JPEG = b"\xff\xd8\xff\xe0 fake jpeg"


@pytest.fixture(autouse=True)
def media(settings, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture(autouse=True)
def no_waiting(monkeypatch) -> None:
    """Пауза между попытками нужна в бою, а тесты она только тормозит."""
    monkeypatch.setattr(generate_images, "PAUSE", 0)


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


def test_torn_connection_is_retried(key, monkeypatch) -> None:
    """Соединение до fal рвётся через раз, а генерация уже оплачена — надо добить."""
    tries: list[int] = []

    def flaky(url: str) -> bytes:
        tries.append(1)
        if len(tries) < 3:
            raise OSError("[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred")
        return JPEG

    monkeypatch.setattr(generate_images, "generate", lambda prompt, api_key: "https://x.test/p.jpg")
    monkeypatch.setattr(generate_images, "download", flaky)
    entry = Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    run()

    entry.refresh_from_db()
    assert len(tries) == 3
    assert bool(entry.image)


def test_rejected_key_is_not_retried(key, monkeypatch) -> None:
    """Повторять 401 — только жечь деньги: ключ от повторов не починится."""
    tries: list[int] = []

    def unauthorised(prompt: str, api_key: str) -> str:
        tries.append(1)
        raise generate_images.urllib.error.HTTPError("u", 401, "no", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(generate_images, "generate", unauthorised)
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    with pytest.raises(CommandError, match="не принят"):
        run()

    assert len(tries) == 1


def test_picture_arrives_inside_the_answer(key, monkeypatch) -> None:
    """`sync_mode` отдаёт картинку data-ссылкой: за ней не надо ходить на CDN."""
    encoded = base64.b64encode(JPEG).decode()
    monkeypatch.setattr(
        generate_images,
        "generate",
        lambda prompt, api_key: f"data:image/jpeg;base64,{encoded}",
    )
    entry = Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    run()

    entry.refresh_from_db()
    assert entry.image.read() == JPEG


@pytest.mark.parametrize(
    "word",
    [
        "девочка",
        "бабушки",
        "дочери",
        "семья",  # женщина в составе, хотя в переводе её нет
        "дети",  # девочка названа в промпте явно
        "готовит (о еде)",
        "мать",
    ],
)
def test_cards_with_women_carry_the_clothing_rule(word: str) -> None:
    assert MODESTY in PROMPTS[word]


@pytest.mark.parametrize(
    "word",
    [
        "сыновья",  # приписка тут добавляла дочерей в кадр
        "отец",
        "полицейский",
        "мальчик",
        "кошка",  # «волос не видно» рядом с кошкой даёт лысую кошку
        "книга",
    ],
)
def test_cards_without_women_stay_clean(word: str) -> None:
    assert MODESTY not in PROMPTS[word]


def test_clothing_rule_names_no_people() -> None:
    """Модель рисует существительные, которые видит.

    Первая версия приписки начиналась словами «every girl and every woman in the
    picture», и модель добавляла девочек туда, где их не просили: у «сыновей»
    появились дочери, у «бабушек» — внучки.
    """
    assert not re.search(r"\b(girl|woman|women|female|child)\w*", MODESTY, re.IGNORECASE)


def test_no_prompt_mentions_kinship() -> None:
    """Слово о родстве тянет за собой вторую сторону.

    «Grandmother» приводит в кадр внучку, «father with sons» — детей обоего пола.
    Поэтому в промптах возраст, пол и количество, а не родственная связь.
    """
    kinship = re.compile(
        r"\b(grandmother|grandfather|father|mother|son|daughter|brother|sister|"
        r"uncle|aunt|niece|nephew|famil|wife|husband)\w*",
        re.IGNORECASE,
    )

    assert [word for word, prompt in PROMPTS.items() if kinship.search(prompt)] == []


def test_no_card_is_in_both_halves() -> None:
    assert set(_WITH_WOMEN) & set(_REST) == set()


def test_both_halves_add_up_to_the_dictionary() -> None:
    """Иначе карточка выпала бы из словаря молча и осталась без картинки."""
    assert len(PROMPTS) == len(_WITH_WOMEN) + len(_REST)


@pytest.fixture(scope="module")
def snapshot() -> list[dict[str, str]]:
    with SNAPSHOT.open(encoding="utf-8") as file:
        return list(csv.DictReader(file))


@needs_snapshot
def test_every_prompt_matches_a_real_card(snapshot: list[dict[str, str]]) -> None:
    """Опечатка в ключе оставила бы карточку без картинки молча."""
    translations = {row["translation_ru"] for row in snapshot}

    assert sorted(key for key in PROMPTS if key not in translations) == []


@pytest.mark.parametrize(
    "word",
    [
        "пять (муж. род)",  # модель ошибается в счёте, а неверное число учит вранью
        "я",
        "почему, зачем",
        "уровень",
        "национальность, гражданство",
    ],
)
def test_undrawable_words_have_no_prompt(word: str) -> None:
    """Список этих слов — решение, а не недоделка: см. причины в pictures."""
    assert word not in PROMPTS
