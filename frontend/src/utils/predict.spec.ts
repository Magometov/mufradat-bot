// #region Imports
// Types
import type { IProgress, IRules } from '../types/progress';

// Utils
import { days, predict } from './predict';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NOW = 1_000_000;
const DAY = 86_400_000;

const rules: IRules = {
    ladder: [1, 3, 7, 16, 35],
    jitter: 10,
    sessionLimit: 20,
    newLimit: 10,
    firstSightLevel: 3,
    needed: 2,
    lapseDrop: 2,
    answersLimit: 100,
};

/**
 * Состояние карточки: ступень, счёт сторон, промахи за жизнь и ступень прошлого падения.
 */
function state(level: number, step = 0, lapses = 0, lapsedFrom = 0): IProgress {
    return { level, step, lapses, lapsedFrom, dueAt: NOW };
}

describe('предсказание срока', () => {
    it.each([
        ['новая', undefined, 0],
        ['знакомая', state(3), 3],
        ['в изучении', state(0, 0, 1), 0],
    ])('первая верная сторона (%s) только считается', (_name, current, level) => {
        expect(predict(current, 'know', rules, NOW)).toMatchObject({
            level,
            step: 1,
            dueAt: NOW,
        });
    });

    it('обе стороны с первого взгляда уводят на свой уровень', () => {
        const first = predict(undefined, 'know', rules, NOW);

        expect(predict(first, 'know', rules, NOW)).toEqual({
            level: 3,
            step: 0,
            lapses: 0,
            lapsedFrom: 0,
            dueAt: NOW + 7 * DAY,
        });
    });

    it('незнакомая падает в изучение со сроком «сейчас»', () => {
        expect(predict(undefined, 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            lapses: 1,
            lapsedFrom: 0,
            dueAt: NOW,
        });
    });

    it('вторая верная сторона в изучении уводит на первый уровень', () => {
        expect(predict(state(0, 1, 1), 'know', rules, NOW)).toEqual({
            level: 1,
            step: 0,
            lapses: 1,
            lapsedFrom: 0,
            dueAt: NOW + DAY,
        });
    });

    it('знакомая поднимается на уровень', () => {
        expect(predict(state(3, 1), 'know', rules, NOW)).toEqual({
            level: 4,
            step: 0,
            lapses: 0,
            lapsedFrom: 0,
            dueAt: NOW + 16 * DAY,
        });
    });

    it('с последнего уровня подниматься некуда', () => {
        expect(predict(state(5, 1), 'know', rules, NOW).level).toBe(5);
    });

    it('забытая знакомая падает в изучение, помня, откуда упала', () => {
        expect(predict(state(4), 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            lapses: 1,
            lapsedFrom: 4,
            dueAt: NOW,
        });
    });

    it('промах в изучении прежнее падение не стирает', () => {
        expect(predict(state(0, 1, 2, 5), 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            lapses: 3,
            lapsedFrom: 5,
            dueAt: NOW,
        });
    });

    it('переученная карточка возвращается ниже прежней ступени', () => {
        expect(predict(state(0, 1, 1, 5), 'know', rules, NOW)).toEqual({
            level: 3,
            step: 0,
            lapses: 1,
            lapsedFrom: 0,
            dueAt: NOW + 7 * DAY,
        });
    });

    it('с нижних ступеней опускаться некуда', () => {
        expect(predict(state(0, 1, 1, 2), 'know', rules, NOW).level).toBe(1);
    });

    it('лестница берётся из правил, а не зашита', () => {
        const other: IRules = { ...rules, ladder: [2, 9], firstSightLevel: 1, needed: 1 };

        expect(predict(undefined, 'know', other, NOW).dueAt).toBe(NOW + 2 * DAY);
        expect(days(2, other)).toBe(9);
    });

    it('сколько сторон закрывают карточку — из правил, а не зашито', () => {
        const other: IRules = { ...rules, needed: 3 };

        expect(predict(state(1, 1), 'know', other, NOW)).toMatchObject({ level: 1, step: 2 });
    });

    it('глубина падения берётся из правил, а не зашита', () => {
        const other: IRules = { ...rules, lapseDrop: 4 };

        expect(predict(state(0, 1, 1, 5), 'know', other, NOW).level).toBe(1);
    });
});
