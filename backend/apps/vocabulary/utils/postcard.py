"""Карточка для чата одной картинкой: слово, перевод, иллюстрация, транслитерация.

Собирается на сервере, потому что в сообщении Telegram сам решает, каким кеглем
показать арабское, и решает мелко.

Арабское рисуется как есть: Pillow собран с raqm и вязь с огласовками строит сам.

Карточка складывается из кусков сверху вниз. Каждый знает свою высоту до того, как
что-то нарисовано, — поэтому холст заводится сразу нужного размера, и подрезать снизу
ничего не приходится.
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from django.core.files.base import File
from PIL import Image, ImageChops, ImageDraw, ImageFont, features

FONTS = Path(__file__).resolve().parent.parent / "fonts"
NASKH = FONTS / "NotoNaskhArabic-Regular.ttf"
SANS = FONTS / "NotoSans-Regular.ttf"

# Версия рисования: поднимаем на единицу всякий раз, когда карточка стала выглядеть иначе.
# Она в имени готового файла, поэтому Telegram и CDN приходят за карточкой заново — по
# прежнему адресу они отдают ту картинку, что скачали когда-то.
DRAWING_VERSION = 2

# Ширина карточки постоянная, высота — по содержимому.
WIDTH = 1000
MARGIN_X = 120
MARGIN_Y = 96

# Кегли строк — те же пропорции, что у оборота карточки в приложении.
ARABIC = 132
TRANSLATION = 66
TRANSLIT = 42

# Отступ сверху у каждого куска и промежуток между строками внутри куска.
GAP = 56
BEFORE_ART = 120
AFTER_ART = 70
LINE_GAP = 0.35

# Короткая черта под переводом — она же в приложении отделяет слово от картинки.
RULE_WIDTH = 115
RULE_HEIGHT = 5

# Иллюстрация вписывается в квадрат со стороной поменьше карточки.
ART_SIDE = 660
ART_RADIUS = 28

# Поля иллюстрации срезаются по цвету угла с этим допуском: фон ровный, но не идеальный.
TRIM = 12

# Палитра приложения, светлая тема.
SURFACE = "#ffffff"
INK = "#111620"
MUTED = "#6d7684"
ACCENT = "#29356b"

QUALITY = 88


def shaped() -> bool:
    """Умеет ли Pillow вязь: без raqm арабское рассыпается на буквы, а огласовки съезжают."""
    return features.check("raqm")


@dataclass(frozen=True, slots=True)
class Part:
    """Кусок карточки: отступ сверху, своя высота и умение лечь на холст."""

    gap: int
    height: int
    paint: Callable[[Image.Image, int], None]


@lru_cache(maxsize=64)
def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Шрифт нужного кегля. Помним прочитанные: подбор кегля читает файл по десять раз."""
    return ImageFont.truetype(str(path), size)


def _room() -> int:
    """Сколько ширины отдано под текст."""
    return WIDTH - MARGIN_X * 2


def _wrapped(text: str, font: ImageFont.FreeTypeFont) -> list[str]:
    """Разбивает строку по словам, чтобы каждая влезала в ширину карточки."""
    lines: list[str] = []
    current = ""

    for word in text.split():
        candidate = f"{current} {word}".strip()

        if current and font.getlength(candidate) > _room():
            lines.append(current)
            current = word
            continue

        current = candidate

    return [*lines, current] if current else lines


def _fitted(text: str, path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Подбирает кегль под самое длинное слово, но ужимает не больше чем вдвое.

    Дальше строку переносят: длинная фраза целиком в строку не влезет никаким кеглем.
    """
    floor = size // 2

    while size > floor:
        font = _font(path, size)

        if all(font.getlength(word) <= _room() for word in text.split()):
            return font

        size -= 6

    return _font(path, size)


def _words(text: str, path: Path, size: int, fill: str, gap: int) -> Part:
    """Кусок из строк текста: подбирает кегль, переносит и считает высоту."""
    font = _fitted(text, path, size)
    lines = _wrapped(text, font)
    boxes = [font.getbbox(line) for line in lines]
    step = int(size * LINE_GAP)

    height = sum(box[3] - box[1] for box in boxes) + step * (len(lines) - 1)

    def paint(canvas: Image.Image, y: int) -> None:
        draw = ImageDraw.Draw(canvas)

        for line, box in zip(lines, boxes, strict=True):
            left = (WIDTH - (box[2] - box[0])) / 2 - box[0]
            draw.text((left, y - box[1]), line, font=font, fill=fill)
            y += box[3] - box[1] + step

    return Part(gap=gap, height=height, paint=paint)


def _rule(gap: int) -> Part:
    """Короткая черта посередине."""

    def paint(canvas: Image.Image, y: int) -> None:
        left, right = (WIDTH - RULE_WIDTH) / 2, (WIDTH + RULE_WIDTH) / 2
        ImageDraw.Draw(canvas).rounded_rectangle(
            [left, y, right, y + RULE_HEIGHT], radius=RULE_HEIGHT // 2, fill=ACCENT
        )

    return Part(gap=gap, height=RULE_HEIGHT, paint=paint)


def _trimmed(picture: Image.Image) -> Image.Image:
    """Срезает ровные поля: модель рисует предмет мелким посреди пустого фона."""
    background = Image.new("RGB", picture.size, picture.getpixel((0, 0)))
    difference = ImageChops.difference(picture, background).convert("L")
    box = difference.point(lambda value: 255 if value > TRIM else 0).getbbox()

    return picture.crop(box) if box else picture


def _art(illustration: File, gap: int) -> Part:
    """Иллюстрация: подрезанная, уменьшенная, со скруглением."""
    picture = _trimmed(Image.open(illustration).convert("RGB"))
    picture.thumbnail((ART_SIDE, ART_SIDE))

    mask = Image.new("L", picture.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *picture.size], radius=ART_RADIUS, fill=255)
    picture.putalpha(mask)

    def paint(canvas: Image.Image, y: int) -> None:
        canvas.paste(picture, (int((WIDTH - picture.width) / 2), y), picture)

    return Part(gap=gap, height=picture.height, paint=paint)


def render(
    *,
    arabic: str,
    translation: str,
    transliteration: str,
    illustration: File | None = None,
) -> bytes:
    """Собирает карточку и отдаёт её джипегом: инлайн Telegram другого не принимает."""
    parts = [
        _words(arabic, NASKH, ARABIC, INK, gap=0),
        _words(translation, SANS, TRANSLATION, INK, gap=GAP),
        _rule(gap=GAP),
    ]

    if illustration is not None:
        parts.append(_art(illustration, gap=BEFORE_ART))

    if transliteration:
        parts.append(_words(transliteration, SANS, TRANSLIT, MUTED, gap=AFTER_ART))

    height = MARGIN_Y * 2 + sum(part.gap + part.height for part in parts)
    canvas = Image.new("RGB", (WIDTH, height), SURFACE)

    y = MARGIN_Y
    for part in parts:
        y += part.gap
        part.paint(canvas, y)
        y += part.height

    buffer = BytesIO()
    canvas.save(buffer, format="JPEG", quality=QUALITY)

    return buffer.getvalue()
