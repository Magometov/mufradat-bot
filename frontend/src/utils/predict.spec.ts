// #region Imports
// Types
import type { IRules } from '../types/progress';

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
};

describe('предсказание срока', () => {
    it('узнанная с первого взгляда уезжает на свой уровень', () => {
        expect(predict(undefined, 'know', rules, NOW)).toEqual({
            level: 3,
            step: 0,
            dueAt: NOW + 7 * DAY,
        });
    });

    it('незнакомая падает в изучение со сроком «сейчас»', () => {
        expect(predict(undefined, 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            dueAt: NOW,
        });
    });

    it('первый верный в изучении только считается', () => {
        expect(predict({ level: 0, step: 0, dueAt: NOW }, 'know', rules, NOW)).toEqual({
            level: 0,
            step: 1,
            dueAt: NOW,
        });
    });

    it('второй верный подряд уводит на первый уровень', () => {
        expect(predict({ level: 0, step: 1, dueAt: NOW }, 'know', rules, NOW)).toEqual({
            level: 1,
            step: 0,
            dueAt: NOW + DAY,
        });
    });

    it('знакомая поднимается на уровень', () => {
        expect(predict({ level: 3, step: 0, dueAt: NOW }, 'know', rules, NOW)).toEqual({
            level: 4,
            step: 0,
            dueAt: NOW + 16 * DAY,
        });
    });

    it('с последнего уровня подниматься некуда', () => {
        expect(predict({ level: 5, step: 0, dueAt: NOW }, 'know', rules, NOW)).toEqual({
            level: 5,
            step: 0,
            dueAt: NOW + 35 * DAY,
        });
    });

    it('забытая знакомая падает в изучение', () => {
        expect(predict({ level: 4, step: 0, dueAt: NOW }, 'forgot', rules, NOW)).toEqual({
            level: 0,
            step: 0,
            dueAt: NOW,
        });
    });

    it('лестница берётся из правил, а не зашита', () => {
        const other: IRules = { ...rules, ladder: [2, 9], firstSightLevel: 1 };

        expect(predict(undefined, 'know', other, NOW).dueAt).toBe(NOW + 2 * DAY);
        expect(days(2, other)).toBe(9);
    });
});
