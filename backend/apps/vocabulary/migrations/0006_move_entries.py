from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

# Флаг `is_word` заменён таблицей: карточка со снятой галочкой была фразой.
SINGULAR = 1


def to_words_and_phrases(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Раскладывает колоду по новым таблицам: слова с одной формой, фразы как есть."""
    Entry = apps.get_model("vocabulary", "Entry")
    Word = apps.get_model("vocabulary", "Word")
    WordForm = apps.get_model("vocabulary", "WordForm")
    Phrase = apps.get_model("vocabulary", "Phrase")

    words: list[object] = []
    phrases: list[object] = []

    for entry in Entry.objects.order_by("pk"):
        if entry.is_word:
            word = Word.objects.create(themes=entry.themes)
            WordForm.objects.create(
                word=word,
                number=SINGULAR,
                arabic=entry.arabic,
                translation_ru=entry.translation_ru,
                transliteration=entry.transliteration,
                # Картинку переносит путь: файл остаётся лежать там же, где лежал.
                image=entry.image.name,
            )
            word.created_at = entry.created_at
            words.append(word)
            continue

        phrase = Phrase.objects.create(
            themes=entry.themes,
            arabic=entry.arabic,
            translation_ru=entry.translation_ru,
            transliteration=entry.transliteration,
            image=entry.image.name,
        )
        phrase.created_at = entry.created_at
        phrases.append(phrase)

    # `auto_now_add` ставит дату при вставке и чужую не принимает, поэтому дата
    # проставляется вторым проходом: `UPDATE` его не трогает.
    Word.objects.bulk_update(words, ["created_at"], batch_size=500)
    Phrase.objects.bulk_update(phrases, ["created_at"], batch_size=500)


def to_entries(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Собирает колоду обратно в `Entry`. Слово с двумя формами даёт две карточки."""
    Entry = apps.get_model("vocabulary", "Entry")
    Word = apps.get_model("vocabulary", "Word")
    Phrase = apps.get_model("vocabulary", "Phrase")

    restored: list[object] = []

    for word in Word.objects.prefetch_related("forms").order_by("pk"):
        for form in word.forms.all():
            entry = Entry.objects.create(
                is_word=True,
                themes=word.themes,
                arabic=form.arabic,
                translation_ru=form.translation_ru,
                transliteration=form.transliteration,
                image=form.image.name,
            )
            entry.created_at = word.created_at
            restored.append(entry)

    for phrase in Phrase.objects.order_by("pk"):
        entry = Entry.objects.create(
            is_word=False,
            themes=phrase.themes,
            arabic=phrase.arabic,
            translation_ru=phrase.translation_ru,
            transliteration=phrase.transliteration,
            image=phrase.image.name,
        )
        entry.created_at = phrase.created_at
        restored.append(entry)

    Entry.objects.bulk_update(restored, ["created_at"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0005_word_wordform_phrase"),
    ]

    operations = [
        migrations.RunPython(to_words_and_phrases, to_entries),
    ]
