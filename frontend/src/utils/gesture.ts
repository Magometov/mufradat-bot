// #region Imports
// Types
import type { IGesture, TGesture } from '../types/swipe';
// #endregion

// Ход короче этого — нажатие: палец никогда не стоит на месте ровно.
export const TAP = 12;
// С этого сдвига ось считается выбранной и до конца жеста уже не меняется.
export const LOCK = 8;
// Доля ширины, за которой медленное утягивание срабатывает.
export const SHARE = 0.14;
// Скорость короткого флика в пикселях на миллисекунду.
export const VELOCITY = 0.3;
// С какого сдвига проявляется метка того, что засчитается.
export const MARK_AT = 16;

/**
 * Чем был жест: нажатием, свайпом в сторону или ничем.
 *
 * Срабатывает и по расстоянию, и по скорости: короткий быстрый флик — такой же осознанный
 * жест, как медленное утягивание. Ось сюда приходит готовой: её выбирают в начале жеста и
 * дальше не меняют, иначе карточка дёргается на дуге, которую рисует большой палец.
 */
export function decide({ dx, dy, ms, width, isSideways }: IGesture): TGesture | null {
    if (Math.abs(dx) < TAP && Math.abs(dy) < TAP) return 'tap';

    if (!isSideways) return null;

    const far = Math.abs(dx) >= width * SHARE;
    const fast = ms > 0 && Math.abs(dx) / ms >= VELOCITY;

    if (!far && !fast) return null;

    return dx < 0 ? 'left' : 'right';
}
