"""Карточка картинкой: вязь, переносы и то, что шрифтам хватает знаков."""

from io import BytesIO

import PIL.features as features
import pytest
from PIL import Image, ImageDraw, ImageFont

from apps.vocabulary.utils import render
from apps.vocabulary.utils.postcard import ARABIC, NASKH, SANS, WIDTH

# Огласовка фатха: ради неё колода и хранит арабское с огласовками.
FATHA = "َ"

WORD = "نَظَّارَة"

# Транслитерация пишется научной латиницей, и этих знаков нет в первой сотне юникода.
SCHOLARLY = "āīūḥṣḍṭẓʿʾ"


def size(data: bytes) -> tuple[int, int]:
    """Размер собранной карточки."""
    return Image.open(BytesIO(data)).size


def drawn(char: str, font: ImageFont.FreeTypeFont) -> bytes:
    """Как выглядит знак, нарисованный этим шрифтом."""
    canvas = Image.new("L", (80, 80), "white")
    ImageDraw.Draw(canvas).text((10, 10), char, font=font, fill="black")

    return canvas.tobytes()


class TestShaping:
    """Вязь строит сам Pillow, и делает это только собранный с raqm."""

    def test_pillow_can_shape_arabic(self):
        """Без raqm буквы рисуются порознь, а огласовки — рядом с буквой, а не над ней."""
        assert features.check_feature("raqm")

    def test_letters_are_joined(self):
        """Буквы соединяются в вязь: слитное слово уже, чем те же буквы порознь."""
        font = ImageFont.truetype(str(NASKH), ARABIC)
        bare = "نظارة"

        assert font.getlength(bare) < sum(font.getlength(letter) for letter in bare)


class TestRender:
    """Собранная карточка: формат, ширина, переносы и высота под содержимое."""

    def test_card_is_a_jpeg_of_the_set_width(self):
        """Инлайн Telegram принимает только джипег, ширина у карточки постоянная."""
        card = render(arabic=WORD, translation="очки", transliteration="nazzara")

        assert card[:2] == b"\xff\xd8"
        assert size(card)[0] == WIDTH

    def test_long_words_are_carried_over(self):
        """Длинная фраза переносится, а не уезжает за край: карточка становится выше."""
        short = render(arabic=WORD, translation="очки", transliteration="")
        long = render(
            arabic="كَيْفَ حَالُكَ يَا صَدِيقِي الْعَزِيز",
            translation="Как твои дела, дорогой друг мой?",
            transliteration="",
        )

        assert size(long)[1] > size(short)[1]

    def test_a_very_long_card_has_no_tail(self):
        """Холст заводится под содержимое: раньше он был фиксирован, и снизу оставалась
        чёрная полоса, как только карточка не влезала."""
        card = Image.open(
            BytesIO(
                render(
                    arabic="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ وَالْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                    translation="Очень длинный перевод, который не помещается в одну строку "
                    "и переносится много раз подряд",
                    transliteration=(
                        "bismi llāhi r-raḥmāni r-raḥīm wa-l-ḥamdu li-llāhi rabbi l-ʿālamīn"
                    ),
                )
            )
        )

        assert card.getpixel((5, card.height - 5)) == (255, 255, 255)

    def test_card_without_a_picture_still_draws(self):
        """У фразы картинки может не быть вовсе."""
        assert render(arabic=WORD, translation="очки", transliteration="nazzara")

    def test_empty_transliteration_leaves_no_room(self):
        """Пустая транслитерация не оставляет за собой пустой полосы."""
        with_it = render(arabic=WORD, translation="очки", transliteration="nazzara")
        without = render(arabic=WORD, translation="очки", transliteration="")

        assert size(without)[1] < size(with_it)[1]


class TestFonts:
    """Шрифты карточки: обрезаны по знакам, и нужные знаки в них есть."""

    @pytest.mark.parametrize("char", list(SCHOLARLY))
    def test_scholarly_latin_has_glyphs(self, char):
        """Шрифт обрезан по знакам, и обрезать его слишком узко — уже случалось.

        Отсутствующий знак рисуется тем же прямоугольником, что и заведомо чужой.
        """
        font = ImageFont.truetype(str(SANS), 48)

        assert drawn(char, font) != drawn("￿", font)

    @pytest.mark.parametrize("char", ["ن", "ظ", FATHA, "ة", "ّ"])
    def test_arabic_has_glyphs(self, char):
        """То же для арабского: огласовки лежат в своём блоке и теряются первыми."""
        font = ImageFont.truetype(str(NASKH), 48)

        assert drawn(char, font) != drawn("￿", font)
