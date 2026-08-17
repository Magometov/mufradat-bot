// #region Imports
// Types
import type { ISessionCard } from '../types/progress';

// Utils
import { RETURN_AFTER, answer } from './session';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NEEDED = 2;

/**
 * Карточка очереди: номер, уровень и счёт верных подряд.
 */
function card(id: string, level = 0, step = 0): ISessionCard {
    return { id, level, step };
}

const ids = (queue: ISessionCard[]): string[] => queue.map((item) => item.id);
const queue = [card('w1'), card('w2'), card('w3'), card('w4'), card('w5')];

describe('очередь сеанса', () => {
    it('забытая карточка возвращается через три другие', () => {
        const next = answer(queue, 'forgot', NEEDED);

        expect(ids(next)).toEqual(['w2', 'w3', 'w4', 'w1', 'w5']);
        expect(next).toHaveLength(queue.length);
    });

    it('первый верный ответ в изучении только считается', () => {
        const next = answer(queue, 'know', NEEDED);

        expect(ids(next)).toEqual(['w2', 'w3', 'w4', 'w1', 'w5']);
        expect(next[RETURN_AFTER]).toEqual(card('w1', 0, 1));
    });

    it('второй верный подряд закрывает карточку', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'know', NEEDED);

        expect(ids(next)).toEqual(['w2']);
    });

    it('промах обнуляет счёт верных', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(card('w1', 0, 0));
    });

    it('знакомая карточка закрывается с первого ответа', () => {
        const next = answer([card('w1', 3), card('w2')], 'know', NEEDED);

        expect(ids(next)).toEqual(['w2']);
    });

    it('забытая знакомая падает в изучение и возвращается', () => {
        const next = answer([card('w1', 4), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(card('w1', 0, 0));
    });

    it('в короткой очереди карточка встаёт в конец', () => {
        const next = answer([card('w1'), card('w2')], 'forgot', NEEDED);

        expect(ids(next)).toEqual(['w2', 'w1']);
    });

    it('последняя карточка, оценённая промахом, остаётся одна', () => {
        expect(ids(answer([card('w1')], 'forgot', NEEDED))).toEqual(['w1']);
    });

    it('последняя закрытая карточка кончает сеанс', () => {
        expect(answer([card('w1', 2)], 'know', NEEDED)).toEqual([]);
    });

    it('пустую очередь оценивать нечем', () => {
        expect(answer([], 'know', NEEDED)).toEqual([]);
    });

    it('число верных ответов задаётся снаружи, а не зашито', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'know', 3);

        expect(next.at(-1)).toEqual(card('w1', 0, 2));
    });
});
