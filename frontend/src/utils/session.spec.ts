// #region Imports
// Types
import type { ISessionCard } from '../types/progress';

// Utils
import { MIN_GAP, RETURN_STEPS, answer } from './session';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NEEDED = 2;
const [FIRST, SECOND, THIRD] = RETURN_STEPS;

/**
 * Карточка очереди: номер, уровень, счёт верных и число промахов.
 */
function card(id: string, level: number | null = 0, step = 0, misses = 0): ISessionCard {
    return { id, level, step, misses };
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

describe('очередь сеанса', () => {
    it('первый промах возвращает через полтора десятка карточек', () => {
        const next = answer(queue(), 'forgot', NEEDED);

        expect(placeOf(next, 'w1')).toBe(FIRST);
        expect(next).toHaveLength(80);
    });

    it('с каждым промахом карточка уходит дальше', () => {
        const once = answer(queue(), 'forgot', NEEDED);
        const twice = answer(once, 'forgot', NEEDED);

        // Второй промах считается по той карточке, что теперь первая, — берём её же.
        const again = answer([card('w1', 0, 0, 1), ...queue().slice(1)], 'forgot', NEEDED);
        const third = answer([card('w1', 0, 0, 2), ...queue().slice(1)], 'forgot', NEEDED);

        expect(placeOf(again, 'w1')).toBe(SECOND);
        expect(placeOf(third, 'w1')).toBe(THIRD);
        expect(twice).toHaveLength(80);
    });

    it('дальше последнего шага не отодвигает', () => {
        const far = answer([card('w1', 0, 0, 9), ...queue().slice(1)], 'forgot', NEEDED);

        expect(placeOf(far, 'w1')).toBe(THIRD);
    });

    it('промахи помнятся в самой карточке', () => {
        const next = answer(queue(), 'forgot', NEEDED);

        expect(next[FIRST]).toEqual(card('w1', 0, 0, 1));
    });

    it('первый верный ответ в изучении только считается', () => {
        const next = answer(queue(), 'know', NEEDED);

        expect(next[FIRST]).toEqual(card('w1', 0, 1, 0));
    });

    it('вспомнил — подтверждение спрашивается скорее, а не дальше', () => {
        const next = answer([card('w1', 0, 0, 1), ...queue().slice(1)], 'know', NEEDED);

        expect(placeOf(next, 'w1')).toBe(FIRST);
    });

    it('второй верный подряд закрывает карточку', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'know', NEEDED);

        expect(ids(next)).toEqual(['w2']);
    });

    it('промах обнуляет счёт верных', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(card('w1', 0, 0, 1));
    });

    it('знакомая карточка закрывается с первого ответа', () => {
        expect(ids(answer([card('w1', 3), card('w2')], 'know', NEEDED))).toEqual(['w2']);
    });

    it('забытая знакомая падает в изучение и возвращается', () => {
        const next = answer([card('w1', 4), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(card('w1', 0, 0, 1));
    });

    it('узнанная с первого взгляда уходит сразу', () => {
        expect(ids(answer([card('w1', null), card('w2')], 'know', NEEDED))).toEqual(['w2']);
    });

    it('незнакомая новая падает в изучение и возвращается', () => {
        const next = answer([card('w1', null), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(card('w1', 0, 0, 1));
    });

    it('промахи подряд не возвращаются кучей', () => {
        const first = answer(queue(), 'forgot', NEEDED);
        const second = answer(first, 'forgot', NEEDED);
        const third = answer(second, 'forgot', NEEDED);

        const places = ['w1', 'w2', 'w3'].map((id) => placeOf(third, id));
        const gaps = [places[1]! - places[0]!, places[2]! - places[1]!];

        expect(places[0]).toBeGreaterThanOrEqual(FIRST - 3);
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

        expect(next[FIRST]).toEqual(card('w1', 0, 2, 0));
    });
});
