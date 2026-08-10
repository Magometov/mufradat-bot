"""Промпты для числительных: рисуется сам знак, а не пять предметов.

Из-за этого числительные и попали в колоду картинок. Считать модель не умеет —
на «пять яблок» она рисует четыре, и карточка учила бы неправильному. А знак «5»
это одна закорючка, тут ошибиться негде.

По той же причине счётные фразы («три книги») рисуются цифрой рядом с предметом:
число несёт знак, а точное количество книг в кадре уже не важно.

Цифры привычные, не восточно-арабские: ٥ и ٦ FLUX путает часто, а в колоде
числительные и так везде словами («хамс»), знака в ней нет вовсе.

Порядковые различаются пьедесталом: единица на первом месте, двойка на втором.
Иначе «первый» и «второй» вышли бы одинаковыми.

Этим карточкам нужен свой стиль: в общем стоит `no text`, что для цифры прямо
противоречит задаче.
"""

_CHARACTER = "as a plump cartoon character with big round eyes and a wide smile"

#: Женская фигура задумана: только сюда приписывается MODESTY.
WITH_WOMEN: dict[str, str] = {
    "три женщины": f"a large digit 3 {_CHARACTER}, beside it a group of adult women",
    "шесть девочек": f"a large digit 6 {_CHARACTER}, beside it a group of girls",
    "девять студенток": f"a large digit 9 {_CHARACTER}, beside young women with backpacks",
}

#: Остальные числительные: цифра сама или цифра рядом с предметом.
REST: dict[str, str] = {
    # --- Сами цифры ------------------------------------------------------------
    "один": f"one single large digit 1 {_CHARACTER}",
    "одна": f"one single large digit 1 {_CHARACTER}",
    "два": f"one single large digit 2 {_CHARACTER}",
    "две": f"one single large digit 2 {_CHARACTER}",
    "три (муж. род)": f"one single large digit 3 {_CHARACTER}",
    "три (жен. род)": f"one single large digit 3 {_CHARACTER}",
    "четыре (муж. род)": f"one single large digit 4 {_CHARACTER}",
    "четыре (жен. род)": f"one single large digit 4 {_CHARACTER}",
    "пять (муж. род)": f"one single large digit 5 {_CHARACTER}",
    "пять (жен. род)": f"one single large digit 5 {_CHARACTER}",
    "шесть (муж. род)": f"one single large digit 6 {_CHARACTER}",
    "шесть (жен. род)": f"one single large digit 6 {_CHARACTER}",
    "семь (муж. род)": f"one single large digit 7 {_CHARACTER}",
    "семь (жен. род)": f"one single large digit 7 {_CHARACTER}",
    "восемь (муж. род)": f"one single large digit 8 {_CHARACTER}",
    "восемь (жен. род)": f"one single large digit 8 {_CHARACTER}",
    "девять (муж. род)": f"one single large digit 9 {_CHARACTER}",
    "девять (жен. род)": f"one single large digit 9 {_CHARACTER}",
    "десять (муж. род)": f"a large number 10 {_CHARACTER}",
    "десять (жен. род)": f"a large number 10 {_CHARACTER}",
    # --- Порядковые: место на пьедестале --------------------------------------
    "первый": f"a digit 1 {_CHARACTER}, standing on the highest step of a winners podium",
    "первая": f"a digit 1 {_CHARACTER}, standing on the highest step of a winners podium",
    "второй": f"a digit 2 {_CHARACTER}, standing on the second step of a winners podium",
    "вторая": f"a digit 2 {_CHARACTER}, standing on the second step of a winners podium",
    "первый урок": f"a digit 1 {_CHARACTER}, beside it an open exercise notebook",
    "второй урок": f"a digit 2 {_CHARACTER}, beside it an open exercise notebook",
    "первый раздел": f"a digit 1 {_CHARACTER}, beside it an open book with a bookmark",
    "второй раздел": f"a digit 2 {_CHARACTER}, beside it an open book with a bookmark",
    "первый урок лёгкий": f"a smiling digit 1 {_CHARACTER}, beside a neat easy notebook",
    "наш первый урок лёгкий": f"a smiling digit 1 {_CHARACTER}, beside a neat easy notebook",
    "второй урок тяжёлый": f"a frowning digit 2 {_CHARACTER}, beside a scribbled hard notebook",
    "первый раздел короткий": f"a digit 1 {_CHARACTER}, beside one thin slim book",
    "второй раздел длинный": f"a digit 2 {_CHARACTER}, beside one very thick fat book",
    # --- Счётные фразы: цифра при предмете ------------------------------------
    "три книги": f"a large digit 3 {_CHARACTER}, beside it a stack of books",
    "четыре ручки": f"a large digit 4 {_CHARACTER}, beside it a handful of pens",
    "пять мальчиков": f"a large digit 5 {_CHARACTER}, beside it a group of boys",
    "шесть дверей": f"a large digit 6 {_CHARACTER}, beside it a row of wooden doors",
    "семь домов": f"a large digit 7 {_CHARACTER}, beside it a row of small houses",
    "восемь студентов": f"a large digit 8 {_CHARACTER}, beside young men with backpacks",
    "девять детей": f"a large digit 9 {_CHARACTER}, beside it a group of small boys",
    "десять мужчин": f"a number 10 {_CHARACTER}, beside it a group of adult men",
    "четыре чемодана": f"a large digit 4 {_CHARACTER}, beside it a pile of suitcases",
    "пять городов": f"a large digit 5 {_CHARACTER}, beside a city skyline of towers",
    "семь автомобилей": f"a large digit 7 {_CHARACTER}, beside it a row of parked cars",
    "восемь столов": f"a large digit 8 {_CHARACTER}, beside it a row of wooden tables",
    "в комнате один студент": f"a digit 1 {_CHARACTER}, beside a young man in a room",
    "в комнате три студента": f"a digit 3 {_CHARACTER}, beside young men in a room",
    "в семье пять детей": f"a digit 5 {_CHARACTER}, beside it a group of small boys",
}
