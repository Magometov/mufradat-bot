// #region Imports
// Types
import type { IGesture } from '../types/swipe';

// Utils
import { SHARE, TAP, VELOCITY, decide } from './gesture';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const WIDTH = 360;
const FAR = WIDTH * SHARE + 1;
const SLOW = 2000;

/**
 * Законченный жест: по умолчанию — поперёк экрана и медленный.
 */
function gesture(fields: Partial<IGesture>): IGesture {
    return { dx: 0, dy: 0, ms: SLOW, width: WIDTH, isSideways: true, ...fields };
}

describe('разбор жеста', () => {
    it('короткий ход — нажатие, даже если ось не выбрана', () => {
        expect(decide(gesture({ dx: TAP - 1, dy: TAP - 1, isSideways: false }))).toBe('tap');
    });

    it('медленное утягивание срабатывает в обе стороны', () => {
        expect(decide(gesture({ dx: FAR }))).toBe('right');
        expect(decide(gesture({ dx: -FAR }))).toBe('left');
    });

    it('короткий быстрый флик срабатывает тоже', () => {
        const dx = VELOCITY * 100 + 1;

        expect(dx).toBeLessThan(WIDTH * SHARE);
        expect(decide(gesture({ dx, ms: 100 }))).toBe('right');
    });

    it('недотянутый медленный ход не срабатывает — карточка вернётся пружиной', () => {
        expect(decide(gesture({ dx: WIDTH * SHARE - 1 }))).toBeNull();
    });

    it('жест вдоль экрана не оценивает: это прокрутка или жест клиента', () => {
        expect(decide(gesture({ dx: FAR, dy: FAR + 10, isSideways: false }))).toBeNull();
    });

    it('нулевая ширина не ломает решение', () => {
        expect(decide(gesture({ dx: FAR, width: 0 }))).toBe('right');
    });

    it('мгновенный ход считается по расстоянию, а не по скорости', () => {
        expect(decide(gesture({ dx: FAR, ms: 0 }))).toBe('right');
    });

    it('порог мягче четверти экрана: большому пальцу так легче', () => {
        expect(SHARE).toBeLessThan(0.2);
        expect(decide(gesture({ dx: WIDTH * 0.15 }))).toBe('right');
    });
});
