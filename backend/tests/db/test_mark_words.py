from io import StringIO

import pytest
from django.core.management import call_command

from apps.vocabulary.models import Entry
from apps.vocabulary.themes import Theme

pytestmark = pytest.mark.django_db


def run(*args: str) -> str:
    out = StringIO()
    call_command("mark_words", *args, stdout=out)
    return out.getvalue()


def test_mark_is_put_on_words_and_left_off_phrases() -> None:
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")
    Entry.objects.create(arabic="هَذَا بَيْتٌ", translation_ru="это дом")

    run()

    assert Entry.objects.get(translation_ru="дом").is_word is True
    assert Entry.objects.get(translation_ru="это дом").is_word is False


def test_second_run_changes_nothing() -> None:
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")
    run()

    assert "изменено: 0" in run()


def test_dry_run_only_shows() -> None:
    Entry.objects.create(arabic="بَيْت", translation_ru="дом")

    output = run("--dry-run")

    assert "изменилось бы: 1" in output
    assert Entry.objects.get(translation_ru="дом").is_word is False


def test_report_counts_words_and_phrases_of_every_theme() -> None:
    """Раскладку по разделам сверяют глазами перед прогоном по живой базе."""
    Entry.objects.create(arabic="بَيْت", translation_ru="дом", themes=[Theme.NOUNS])
    Entry.objects.create(arabic="هَذَا بَيْتٌ", translation_ru="это дом", themes=[Theme.NOUNS])
    Entry.objects.create(arabic="كِتَاب", translation_ru="книга", themes=[Theme.NOUNS])

    line = next(row for row in run().splitlines() if "Существительные" in row)

    assert line.split()[-2:] == ["2", "1"]
