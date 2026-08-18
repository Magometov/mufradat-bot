// #region Imports
// Utils
import { cardWord, dayWord, sectionWord, timeWord, wordWord } from './plural';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

describe('склонение дней', () => {
    it('единственное число', () => {
        expect(dayWord(1)).toBe('день');
        expect(dayWord(21)).toBe('день');
    });

    it('от двух до четырёх', () => {
        expect(dayWord(3)).toBe('дня');
        expect(dayWord(34)).toBe('дня');
    });

    it('множественное', () => {
        expect(dayWord(7)).toBe('дней');
        expect(dayWord(35)).toBe('дней');
    });

    it('вторая десятка — всегда «дней»', () => {
        expect(dayWord(11)).toBe('дней');
        expect(dayWord(16)).toBe('дней');
    });
});

describe('склонение прочих слов', () => {
    it('карточки', () => {
        expect(cardWord(1)).toBe('карточка');
        expect(cardWord(294)).toBe('карточки');
        expect(cardWord(337)).toBe('карточек');
        expect(cardWord(11)).toBe('карточек');
    });

    it('слова', () => {
        expect(wordWord(1)).toBe('слово');
        expect(wordWord(2)).toBe('слова');
        expect(wordWord(8)).toBe('слов');
    });

    it('разы — столько подтверждений нужно карточке', () => {
        expect(timeWord(1)).toBe('раз');
        expect(timeWord(2)).toBe('раза');
        expect(timeWord(5)).toBe('раз');
    });

    it('разделы — всегда после «из», поэтому родительный', () => {
        expect(sectionWord(1)).toBe('раздела');
        expect(sectionWord(8)).toBe('разделов');
    });
});
