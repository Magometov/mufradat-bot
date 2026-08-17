// #region Imports
// Utils
import { SHARE, TAP, VELOCITY, decide } from './gesture';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const WIDTH = 360;
const FAR = WIDTH * SHARE + 1;
const SLOW = 2000;

describe('разбор жеста', () => {
    it('короткий ход — нажатие', () => {
        expect(decide(TAP - 1, TAP - 1, 100, WIDTH)).toBe('tap');
    });

    it('медленное утягивание за четверть экрана срабатывает', () => {
        expect(decide(FAR, 0, SLOW, WIDTH)).toBe('right');
        expect(decide(-FAR, 0, SLOW, WIDTH)).toBe('left');
    });

    it('короткий быстрый флик срабатывает тоже', () => {
        const dx = VELOCITY * 100 + 1;

        expect(dx).toBeLessThan(WIDTH * SHARE);
        expect(decide(dx, 0, 100, WIDTH)).toBe('right');
    });

    it('недотянутый медленный ход не срабатывает — карточка вернётся пружиной', () => {
        expect(decide(WIDTH * SHARE - 1, 0, SLOW, WIDTH)).toBeNull();
    });

    it('вертикаль остаётся странице и клиенту Telegram', () => {
        expect(decide(FAR, FAR + 10, SLOW, WIDTH)).toBeNull();
    });

    it('нулевая ширина не ломает решение', () => {
        expect(decide(FAR, 0, SLOW, 0)).toBe('right');
    });

    it('мгновенный ход считается по расстоянию, а не по скорости', () => {
        expect(decide(FAR, 0, 0, WIDTH)).toBe('right');
    });
});
