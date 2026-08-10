"""Промпты для рисования картинок к карточкам.

Словарь `PROMPTS` заодно и белый список: карточку без записи в нём команда не
трогает. Так решается «не всем нужна картинка» — списком, который видно глазами,
а не догадками по переводу. Причины, по которым та или иная группа слов картинки
не получает, перечислены в `words`, `phrases` и `numbers`.

Значения `PROMPTS` — готовые промпты целиком, вместе с приписками. Собирать их
на стороне команды было ошибкой: приписку стиля не было видно ни в `--dry-run`,
ни в тестах, а цифрам нужен свой стиль, и в команде развилке места нет.

Промпты английские: FLUX по-русски рисует мимо. Ключ — перевод ровно как в базе,
вместе с пометкой в скобках: «врач (муж. род)» и «врач (жен. род)» должны
получить разные картинки.

Два правила письма промптов, оба выведены из испорченных картинок:

1. Модель не понимает кванторов и условий — она рисует существительные, которые
   видит. Первая версия приписки про хиджаб начиналась словами «every girl and
   every woman in the picture», и модель послушно добавляла девочек туда, где их
   не просили: у «сыновей» появились дочери, у «бабушек» — внучки. Поэтому
   `MODESTY` не называет женщин, а описывает только одежду, и приписывается лишь
   к тем промптам, где женщина задумана.

2. Слово о родстве тянет за собой вторую сторону: «grandmother» приводит внучку,
   «father with sons» — детей обоего пола. Поэтому в промптах не родство, а
   возраст, пол и количество: не «three grandmothers», а «three elderly women».
"""

from apps.vocabulary.pictures import numbers, phrases, words

#: Общий стиль колоды. Без него у каждой картинки свой фон и своя манера.
#: `no text` обязателен — модель иначе лезет подписывать рисунок исковерканными
#: буквами.
STYLE = "cartoon illustration, Islamic setting, plain background, no text"

#: Стиль для числительных: там знак и есть содержание карточки, и запрет на текст
#: из общего стиля прямо противоречил бы задаче.
DIGIT_STYLE = (
    "cartoon illustration, Islamic setting, plain background, "
    "the digit is the only symbol in the picture"
)

#: Одежда женских фигур, требование владельца. Ни одного существительного о людях:
#: назвать здесь «girl» или «woman» — значит попросить модель её нарисовать.
MODESTY = "in a hijab and modest long clothing"

#: Откуда что берётся и каким стилем рисуется.
_SOURCES = ((words, STYLE), (phrases, STYLE), (numbers, DIGIT_STYLE))

#: Промпты, где женщина или девочка задумана: только им приписывается `MODESTY`.
_WITH_WOMEN: dict[str, str] = {
    word: body for module, _ in _SOURCES for word, body in module.WITH_WOMEN.items()
}

#: Все остальные — предметы, животные и картинки, где люди только мужского пола.
_REST: dict[str, str] = {word: body for module, _ in _SOURCES for word, body in module.REST.items()}


def _assemble(body: str, style: str, *, has_women: bool) -> str:
    parts = [body, MODESTY, style] if has_women else [body, style]

    return ", ".join(parts)


PROMPTS: dict[str, str] = {
    word: _assemble(body, style, has_women=word in module.WITH_WOMEN)
    for module, style in _SOURCES
    for word, body in {**module.REST, **module.WITH_WOMEN}.items()
}
