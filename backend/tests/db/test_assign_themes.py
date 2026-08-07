import pytest
from django.core.management import call_command

from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme

pytestmark = pytest.mark.django_db


def run(*args: str) -> str:
    from io import StringIO

    out = StringIO()
    call_command("assign_themes", *args, stdout=out)
    return out.getvalue()


def test_themes_are_written_to_every_word() -> None:
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    Entry.objects.create(arabic="أُسْرَتِي كَبِيرَةٌ", translation_ru="моя семья большая")

    run()

    assert Entry.objects.get(translation_ru="верблюд").themes == [Theme.NOUNS]
    assert Entry.objects.get(translation_ru="моя семья большая").themes == [
        Theme.FAMILY,
        Theme.ANTONYMS,
    ]


def test_second_run_changes_nothing() -> None:
    """Команду будут запускать после каждого пополнения базы — она должна быть повторяемой."""
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")
    run()

    assert "изменено: 0" in run()


def test_dry_run_only_shows() -> None:
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд")

    output = run("--dry-run")

    assert "изменилось бы: 1" in output
    assert Entry.objects.get(translation_ru="верблюд").themes == []


def test_keep_manual_leaves_hand_picked_themes() -> None:
    """Владелец мог поправить темы в админке — скрипт не должен это затирать."""
    Entry.objects.create(arabic="جَمَل", translation_ru="верблюд", themes=[Theme.GREETINGS])

    run("--keep-manual")

    assert Entry.objects.get(translation_ru="верблюд").themes == [Theme.GREETINGS]


def test_phrases_left_in_the_fallback_theme_are_listed() -> None:
    """Остаток надо видеть глазами: иначе непонятно, где правила не сработали."""
    Entry.objects.create(arabic="بَابُ الْبَيْتِ", translation_ru="дверь дома")

    output = run()

    assert "дверь дома" in output.split("Фраз только")[1]
