// #region Imports
// Types
import type { IEntry } from '../types/entry';
import type { IProgress } from '../types/progress';

// Utils
import { countDue, nextDueAt, soonText, summarize } from './due';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const DAY = 86_400_000;
// Полдень: у краёв суток «завтра» и «сегодня» считаются по календарю, а не по разнице.
const NOON = new Date(2026, 7, 17, 12).getTime();

/**
 * Карточка колоды: для этих подсчётов важен только номер.
 */
function entry(id: string): IEntry {
    return {
        id,
        arabic: 'كِتَاب',
        translation_ru: 'книга',
        transliteration: '',
        is_word: true,
        image: null,
        image_width: null,
        image_height: null,
        themes: [],
    };
}

function state(dueAt: number): IProgress {
    return { level: 3, step: 0, dueAt };
}

const deck = ['w1', 'w2', 'w3'].map(entry);

describe('сколько на сегодня', () => {
    it('новые считаются: их ещё не видели', () => {
        expect(countDue(deck, new Map(), NOON)).toBe(3);
    });

    it('срок в будущем не считается', () => {
        const progress = new Map([
            ['w1', state(NOON + DAY)],
            ['w2', state(NOON - DAY)],
        ]);

        expect(countDue(deck, progress, NOON)).toBe(2);
    });

    it('пустая колода даёт нуль', () => {
        expect(countDue([], new Map(), NOON)).toBe(0);
    });
});

describe('когда ближайшая', () => {
    it('берётся самый ранний срок', () => {
        const progress = new Map([
            ['w1', state(NOON + 3 * DAY)],
            ['w2', state(NOON + DAY)],
        ]);

        expect(nextDueAt(deck, progress)).toBe(NOON + DAY);
    });

    it('без состояний срока нет', () => {
        expect(nextDueAt(deck, new Map())).toBeNull();
    });
});

describe('когда это словами', () => {
    it('сегодня, завтра и послезавтра названы словами', () => {
        expect(soonText(NOON + 2 * 3600_000, NOON)).toBe('сегодня');
        expect(soonText(NOON + DAY, NOON)).toBe('завтра');
        expect(soonText(NOON + 2 * DAY, NOON)).toBe('послезавтра');
    });

    it('дальше — числом с правильным словом', () => {
        expect(soonText(NOON + 4 * DAY, NOON)).toBe('через 4 дня');
        expect(soonText(NOON + 7 * DAY, NOON)).toBe('через 7 дней');
    });

    it('раннее утро следующих суток — это завтра, а не «через 0»', () => {
        const morning = new Date(2026, 7, 18, 7).getTime();

        expect(soonText(morning, NOON)).toBe('завтра');
    });

    it('просроченное — сегодня', () => {
        expect(soonText(NOON - 5 * DAY, NOON)).toBe('сегодня');
    });
});

describe('итог сеанса', () => {
    it('группирует по срокам, дальние первыми', () => {
        const progress = new Map([
            ['w1', state(NOON + 7 * DAY)],
            ['w2', state(NOON + 7 * DAY)],
            ['w3', state(NOON + DAY)],
        ]);

        expect(summarize(['w1', 'w2', 'w3'], progress, NOON)).toBe(
            '2 слова вернутся через 7 дней, 1 — завтра.',
        );
    });

    it('карточки без состояния в итог не попадают', () => {
        const progress = new Map([['w1', state(NOON + DAY)]]);

        expect(summarize(['w1', 'w2'], progress, NOON)).toBe('1 слово вернётся завтра.');
    });

    it('сеанс без оценок так и говорит', () => {
        expect(summarize(['w1'], new Map(), NOON)).toBe('Оценок в этом сеансе не было.');
    });
});
