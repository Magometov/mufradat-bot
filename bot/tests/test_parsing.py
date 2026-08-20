"""Разбор вставки: что отсеивается как уже лежащее в колоде."""

from bot.parsing import Card, Group, without_known


def word(translation: str, arabic: str, number: int = 1) -> Card:
    """Карточка слова из вставки."""
    return Card(
        translation_ru=translation,
        transliteration="",
        arabic=arabic,
        prompt="",
        number=number,
    )


class TestWithoutKnown:
    """Отсев повторов: карточка уходит из вставки, единица без карточек — целиком."""

    def test_known_card_leaves_the_paste(self):
        """Совпавшая пара «арабское — перевод» из вставки убирается, остальные остаются."""
        groups = [Group(cards=[word("книга", "كِتَاب"), word("книги", "كُتُب", number=2)])]

        left, dropped = without_known(groups, {("كِتَاب", "книга")})

        assert [card.translation_ru for card in left[0].cards] == ["книги"]
        assert dropped == ["книга"]

    def test_unit_without_cards_goes_away(self):
        """Единица, у которой не осталось ни одной карточки, из вставки уходит вся."""
        groups = [Group(cards=[word("книга", "كِتَاب")]), Group(cards=[word("дом", "بَيْت")])]

        left, dropped = without_known(groups, {("كِتَاب", "книга")})

        assert [group.title for group in left] == ["дом"]
        assert dropped == ["книга"]

    def test_nothing_known_keeps_the_paste(self):
        """Ничего не совпало — вставка идёт как есть."""
        groups = [Group(cards=[word("книга", "كِتَاب")])]

        left, dropped = without_known(groups, set())

        assert left == groups
        assert dropped == []

    def test_halves_of_different_cards_are_not_a_match(self):
        """Совпасть должны обе половины пары: арабское от одной, перевод от другой — не повтор."""
        groups = [Group(cards=[word("книга", "كِتَاب")])]

        left, dropped = without_known(groups, {("بَيْت", "книга"), ("كِتَاب", "дом")})

        assert left == groups
        assert dropped == []
