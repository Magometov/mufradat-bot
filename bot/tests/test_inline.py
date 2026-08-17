"""Результаты инлайна: чем карточка с картинкой отличается от карточки без неё."""

from dataclasses import replace

from aiogram.types import InlineQueryResultArticle, InlineQueryResultPhoto

from bot.api import Found
from bot.handlers.inline import as_result

CARD = Found(
    id="w12",
    arabic="قَلَم",
    translation_ru="ручка",
    transliteration="qalam",
    image="https://mufradat.example/m/cards/w12.webp",
    width=1024,
    height=1024,
)


def test_card_with_a_picture_goes_as_a_photo():
    """С картинкой карточка уезжает картинкой с подписью."""
    item = as_result(CARD)

    assert isinstance(item, InlineQueryResultPhoto)
    assert item.photo_url == CARD.image
    assert item.thumbnail_url == CARD.image
    assert item.caption == "قَلَم\n\nручка\nqalam"


def test_the_picture_carries_its_size():
    """Размеры едут с картинкой: по ним Telegram раскладывает список выбора."""
    item = as_result(CARD)

    assert (item.photo_width, item.photo_height) == (1024, 1024)


def test_card_without_a_picture_goes_as_text():
    """Без картинки — текстом, с тем же содержимым."""
    item = as_result(replace(CARD, image=None))

    assert isinstance(item, InlineQueryResultArticle)
    assert item.input_message_content.message_text == "قَلَم\n\nручка\nqalam"


def test_the_number_becomes_the_result_id():
    """Номер карточки и есть номер результата: он должен быть свой у каждой строки."""
    assert as_result(CARD).id == "w12"


def test_markup_characters_are_escaped():
    """«&» и «<» в переводе не должны ломать разметку сообщения."""
    item = as_result(replace(CARD, translation_ru="сложно & просто"))

    assert "&amp;" in item.caption
