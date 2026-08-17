// #region Imports
// Types
import type { TGesture } from '../types/swipe';
// #endregion

// Ход короче этого — нажатие: палец никогда не стоит на месте ровно.
export const TAP = 12;
// Доля ширины, за которой медленное утягивание срабатывает.
export const SHARE = 0.22;
// Скорость короткого флика в пикселях на миллисекунду.
export const VELOCITY = 0.5;

/**
 * Чем был жест: нажатием, свайпом в сторону или ничем.
 *
 * Срабатывает и по расстоянию, и по скорости: короткий быстрый флик — такой же
 * осознанный жест, как медленное утягивание за четверть экрана.
 */
export function decide(dx: number, dy: number, ms: number, width: number): TGesture | null {
    if (Math.abs(dx) < TAP && Math.abs(dy) < TAP) return 'tap';

    // Вертикаль не наша: это прокрутка длинной карточки и жесты клиента Telegram.
    if (Math.abs(dx) <= Math.abs(dy)) return null;

    const far = Math.abs(dx) >= width * SHARE;
    const fast = ms > 0 && Math.abs(dx) / ms >= VELOCITY;

    if (!far && !fast) return null;

    return dx < 0 ? 'left' : 'right';
}
