// #region Imports
// Utils
import { dayWord } from './plural';

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
