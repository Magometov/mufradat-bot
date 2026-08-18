// #region Imports
// Types
import type { ISessionCard } from '../types/progress';

// Utils
import { MIN_GAP, RETURN_STEPS, SPREAD, answer, isReversedAt } from './session';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NEEDED = 2;
const [FIRST, SECOND, THIRD] = RETURN_STEPS;

/**
 * Карточка очереди: номер, уровень, счёт верных, число промахов и сторона.
 */
function card(
    id: string,
    level: number | null = 0,
    step = 0,
    misses = 0,
    isReversed = false,
): ISessionCard {
    return { id, isReversed, level, step, misses };
}

/**
 * Та же карточка после возврата: сторона у неё уже перевёрнута.
 */
function returned(id: string, level: number | null = 0, step = 0, misses = 0): ISessionCard {
    return card(id, level, step, misses, true);
}

const ids = (queue: ISessionCard[]): string[] => queue.map((item) => item.id);

/**
 * Длинная очередь: в короткой карточка встаёт в конец и шаг не проверить.
 */
function queue(size = 80): ISessionCard[] {
    return Array.from({ length: size }, (_, index) => card(`w${index + 1}`));
}

/**
 * На каком месте в новой очереди оказалась карточка.
 */
function placeOf(next: ISessionCard[], id: string): number {
    return ids(next).indexOf(id);
}

/**
 * Карточка очереди по номеру: место у неё разное, а содержимое проверяется всегда.
 */
function found(next: ISessionCard[], id: string): ISessionCard | undefined {
    return next.find((item) => item.id === id);
}

/**
 * Легла ли карточка в вилку своего шага: не ближе порога и не дальше разброса.
 */
function within(next: ISessionCard[], id: string, floor: number): boolean {
    const place = placeOf(next, id);

    return place >= floor && place <= floor + floor * SPREAD;
}

describe('сторона карточки', () => {
    it.each([
        [1, true],
        [2, false],
        [3, true],
        [4, false],
        [5, true],
    ])('ступень %i спрашивается своей стороной', (level, isReversed) => {
        expect(isReversedAt(level)).toBe(isReversed);
    });

    it('изучение начинается арабской стороной, а возврат даёт русскую', () => {
        const next = answer(
            [{ ...card('w1'), isReversed: isReversedAt(0) }, ...queue().slice(1)],
            'forgot',
            NEEDED,
        );

        expect(isReversedAt(0)).toBe(false);
        expect(found(next, 'w1')?.isReversed).toBe(true);
    });

    it('новая карточка показывается арабской стороной', () => {
        // Русским вперёд её не вспомнить: слово ещё ни разу не видели.
        expect(isReversedAt(null)).toBe(false);
    });
});

describe('очередь сеанса', () => {
    it('первый промах возвращает через полтора десятка карточек', () => {
        const next = answer(queue(), 'forgot', NEEDED);

        expect(within(next, 'w1', FIRST!)).toBe(true);
        expect(next).toHaveLength(80);
    });

    it('одна и та же карточка возвращается на разные места', () => {
        const places = new Set(
            Array.from({ length: 20 }, () => placeOf(answer(queue(), 'forgot', NEEDED), 'w1')),
        );

        // Ритма быть не должно: шаг мажется разбросом, а не отсчитывается ровно.
        expect(places.size).toBeGreaterThan(1);
    });

    it('с каждым промахом карточка уходит дальше', () => {
        const once = answer(queue(), 'forgot', NEEDED);
        const twice = answer(once, 'forgot', NEEDED);

        // Второй промах считается по той карточке, что теперь первая, — берём её же.
        const again = answer([card('w1', 0, 0, 1), ...queue().slice(1)], 'forgot', NEEDED);
        const third = answer([card('w1', 0, 0, 2), ...queue().slice(1)], 'forgot', NEEDED);

        expect(within(again, 'w1', SECOND!)).toBe(true);
        expect(within(third, 'w1', THIRD!)).toBe(true);
        expect(twice).toHaveLength(80);
    });

    it('дальше последнего шага не отодвигает', () => {
        const far = answer([card('w1', 0, 0, 9), ...queue().slice(1)], 'forgot', NEEDED);

        expect(within(far, 'w1', THIRD!)).toBe(true);
    });

    it('возврат спрашивает слово другой стороной', () => {
        const once = answer(queue(), 'forgot', NEEDED);
        const twice = answer([card('w1', 0, 0, 1, true), ...queue().slice(1)], 'forgot', NEEDED);

        expect(found(once, 'w1')?.isReversed).toBe(true);
        expect(found(twice, 'w1')?.isReversed).toBe(false);
    });

    it('промахи помнятся в самой карточке', () => {
        const next = answer(queue(), 'forgot', NEEDED);

        expect(found(next, 'w1')).toEqual(returned('w1', 0, 0, 1));
    });

    it('первый верный ответ в изучении только считается', () => {
        const next = answer(queue(), 'know', NEEDED);

        expect(found(next, 'w1')).toEqual(returned('w1', 0, 1, 0));
    });

    it('вспомнил — подтверждение спрашивается скорее, а не дальше', () => {
        const next = answer([card('w1', 0, 0, 1), ...queue().slice(1)], 'know', NEEDED);

        expect(within(next, 'w1', FIRST!)).toBe(true);
    });

    it('второй верный подряд закрывает карточку', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'know', NEEDED);

        expect(ids(next)).toEqual(['w2']);
    });

    it('промах обнуляет счёт верных', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(returned('w1', 0, 0, 1));
    });

    it('знакомая карточка закрывается с первого ответа', () => {
        expect(ids(answer([card('w1', 3), card('w2')], 'know', NEEDED))).toEqual(['w2']);
    });

    it('забытая знакомая падает в изучение и возвращается', () => {
        const next = answer([card('w1', 4), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(returned('w1', 0, 0, 1));
    });

    it('узнанная с первого взгляда уходит сразу', () => {
        expect(ids(answer([card('w1', null), card('w2')], 'know', NEEDED))).toEqual(['w2']);
    });

    it('незнакомая новая падает в изучение и возвращается', () => {
        const next = answer([card('w1', null), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(returned('w1', 0, 0, 1));
    });

    it('промахи подряд не возвращаются кучей', () => {
        const first = answer(queue(), 'forgot', NEEDED);
        const second = answer(first, 'forgot', NEEDED);
        const third = answer(second, 'forgot', NEEDED);

        // Порядок возвратов разбросом не задан — важно, что они не встали вплотную.
        const places = ['w1', 'w2', 'w3']
            .map((id) => placeOf(third, id))
            .sort((first, second) => first - second);
        const gaps = [places[1]! - places[0]!, places[2]! - places[1]!];

        expect(places[0]).toBeGreaterThanOrEqual(FIRST! - 3);
        expect(gaps.every((gap) => gap > MIN_GAP)).toBe(true);
    });

    it('в короткой очереди карточка встаёт в конец', () => {
        expect(ids(answer([card('w1'), card('w2')], 'forgot', NEEDED))).toEqual(['w2', 'w1']);
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
        const next = answer([card('w1', 0, 1), ...queue().slice(1)], 'know', 3);

        expect(found(next, 'w1')).toEqual(returned('w1', 0, 2, 0));
    });
});
