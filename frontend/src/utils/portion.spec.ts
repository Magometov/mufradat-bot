// #region Imports
// Types
import type { IEntry } from '../types/entry';
import type { IProgress } from '../types/progress';

// Utils
import { buildPortion } from './portion';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NOW = 1_000_000;
const DAY = 86_400_000;

/**
 * Карточка колоды: для сборки порции важен только номер.
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
        themes: ['numbers'],
    };
}

/**
 * Состояние карточки: уровень, счёт и срок в миллисекундах.
 */
function state(level: number, dueAt: number, step = 0): IProgress {
    return { level, step, dueAt };
}

const deck = ['w1', 'w2', 'w3', 'w4', 'w5'].map(entry);
const ids = (portion: IEntry[]): string[] => portion.map((item) => item.id);

describe('сборка порции', () => {
    it('ставит изучение вперёд просроченных, а новые в конец', () => {
        const progress = new Map([
            ['w1', state(3, NOW - DAY)],
            ['w2', state(0, NOW)],
            ['w3', state(2, NOW - 2 * DAY)],
        ]);

        expect(ids(buildPortion(deck, progress, NOW, null))).toEqual([
            'w2',
            'w3',
            'w1',
            'w4',
            'w5',
        ]);
    });

    it('не берёт карточки, чей срок ещё не подошёл', () => {
        const progress = new Map([
            ['w1', state(3, NOW + DAY)],
            ['w2', state(4, NOW + 10 * DAY)],
        ]);

        expect(ids(buildPortion(deck, progress, NOW, null))).toEqual(['w3', 'w4', 'w5']);
    });

    it('без потолков отдаёт весь раздел', () => {
        expect(buildPortion(deck, new Map(), NOW, null)).toHaveLength(5);
    });

    it('с потолком режет сеанс и ограничивает новые', () => {
        const portion = buildPortion(deck, new Map(), NOW, { sessionLimit: 4, newLimit: 2 });

        expect(ids(portion)).toEqual(['w1', 'w2']);
    });

    it('в день с возвратами новых не берёт вовсе', () => {
        const progress = new Map([
            ['w1', state(0, NOW)],
            ['w2', state(0, NOW)],
            ['w3', state(3, NOW - DAY)],
        ]);

        const portion = buildPortion(deck, progress, NOW, { sessionLimit: 3, newLimit: 10 });

        expect(ids(portion)).toEqual(['w1', 'w2', 'w3']);
    });

    it('давно просроченные идут первыми', () => {
        const progress = new Map([
            ['w1', state(3, NOW - DAY)],
            ['w2', state(3, NOW - 5 * DAY)],
            ['w3', state(3, NOW - 3 * DAY)],
        ]);

        const portion = buildPortion(deck, progress, NOW, { sessionLimit: 2, newLimit: 0 });

        expect(ids(portion)).toEqual(['w2', 'w3']);
    });

    it('пустая колода даёт пустую порцию', () => {
        expect(buildPortion([], new Map(), NOW, { sessionLimit: 20, newLimit: 10 })).toEqual([]);
    });
});
