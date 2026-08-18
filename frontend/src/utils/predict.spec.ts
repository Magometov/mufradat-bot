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
 * Состояние карточки: ступень, счёт верных и ступень прошлого падения.
 */
function state(level: number, step = 0, lapsedFrom = 0): IProgress {
    return { level, step, lapsedFrom, dueAt: NOW };
}

describe('предсказание срока', () => {
    it('узнанная с первого взгляда уезжает на свой уровень', () => {
        expect(predict(undefined, 'know', rules, NOW)).toEqual({
            level: 3,
            step: 0,
            lapsedFrom: 0,
            dueAt: NOW + 7 * DAY,
        });
    });

    it('незнакомая падает в изучение со сроком «сейчас»', () => {
        expect(predict(undefined, 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            lapsedFrom: 0,
            dueAt: NOW,
        });
    });

    it('первый верный в изучении только считается', () => {
        expect(predict(state(0), 'know', rules, NOW)).toEqual({
            level: 0,
            step: 1,
            lapsedFrom: 0,
            dueAt: NOW,
        });
    });

    it('второй верный подряд уводит на первый уровень', () => {
        expect(predict(state(0, 1), 'know', rules, NOW)).toEqual({
            level: 1,
            step: 0,
            lapsedFrom: 0,
            dueAt: NOW + DAY,
        });
    });

    it('знакомая поднимается на уровень', () => {
        expect(predict(state(3), 'know', rules, NOW)).toEqual({
            level: 4,
            step: 0,
            lapsedFrom: 0,
            dueAt: NOW + 16 * DAY,
        });
    });

    it('с последнего уровня подниматься некуда', () => {
        expect(predict(state(5), 'know', rules, NOW)).toEqual({
            level: 5,
            step: 0,
            lapsedFrom: 0,
            dueAt: NOW + 35 * DAY,
        });
    });

    it('забытая знакомая падает в изучение, помня, откуда упала', () => {
        expect(predict(state(4), 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            lapsedFrom: 4,
            dueAt: NOW,
        });
    });

    it('промах в изучении прежнее падение не стирает', () => {
        expect(predict(state(0, 1, 5), 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            lapsedFrom: 5,
            dueAt: NOW,
        });
    });

    it('переученная карточка возвращается ниже прежней ступени', () => {
        expect(predict(state(0, 1, 5), 'know', rules, NOW)).toEqual({
            level: 3,
            step: 0,
            lapsedFrom: 0,
            dueAt: NOW + 7 * DAY,
        });
    });

    it('с нижних ступеней опускаться некуда', () => {
        expect(predict(state(0, 1, 2), 'know', rules, NOW).level).toBe(1);
    });

    it('лестница берётся из правил, а не зашита', () => {
        const other: IRules = { ...rules, ladder: [2, 9], firstSightLevel: 1 };

        expect(predict(undefined, 'know', other, NOW).dueAt).toBe(NOW + 2 * DAY);
        expect(days(2, other)).toBe(9);
    });

    it('глубина падения берётся из правил, а не зашита', () => {
        const other: IRules = { ...rules, lapseDrop: 4 };

        expect(predict(state(0, 1, 5), 'know', other, NOW).level).toBe(1);
    });
});
