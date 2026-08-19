// #region Imports
// Types
import type { ISessionCard, TVerdict } from '../types/progress';

// Utils
import { LEARNING } from './levels';
// #endregion

// Средний зазор до возврата, в карточках. Число, а не доля колоды: память не знает,
// сколько слов в разделе, — ей важно, сколько чужих прошло между двумя показами. Доля
// давала бы шесть карточек на колоде в полтора десятка и тысячу на колоде в две с
// половиной.

// Слово, которое далось: вторую сторону спрашиваем далеко.
export const GAP_AFTER_KNOW = 40;

// Слово, которое не далось: близко, но с каждым промахом дальше — иначе оно мелькает
// перед глазами. Промахов больше, чем зазоров, — берётся последний.
export const GAP_AFTER_MISS = [10, 20, 40];

// Ближе слово не вернётся ни при каком зазоре: на таком расстоянии «помню» ещё говорится
// памятью о прошлой карточке, а не о самом слове.
export const MIN_AHEAD = 6;

// Дальше половины остатка не отодвигаем: на короткой очереди зазор в четыре десятка
// значит «в самый конец», и сеанс распадается на круг новых и круг повторов.
const FURTHEST = 0.5;

/**
 * Спрашивать ли карточку русским вперёд.
 *
 * Нечётная ступень спрашивает русским, чётная — арабским, а подтверждённая сторона
 * сдвигает счёт на единицу: сеанс могли бросить между сторонами, и вторая ждёт в
 * следующем заходе. Новую карточку спрашиваем арабским: русским вперёд её не
 * вспомнить, такой показ был бы промахом наверняка.
 */
export function isReversedAt(level: number | null, step: number): boolean {
    return ((level ?? LEARNING) + step) % 2 === 1;
}

/**
 * Очередь сеанса после оценки первой карточки.
 *
 * Карточка уходит из очереди, только подтвердив все стороны: пока подтверждена не
 * всякая, она возвращается — как и забытая, но та тем дальше, чем чаще не давалась.
 * Счёт сторон здесь считается только чтобы решить, закрылась ли карточка; настоящие
 * уровень и срок пишет сервер.
 */
export function answer<TCard extends ISessionCard>(
    queue: TCard[],
    verdict: TVerdict,
    needed: number,
): TCard[] {
    const [card, ...rest] = queue;

    if (card === undefined) return [];

    if (verdict === 'forgot') {
        const misses = card.misses + 1;

        return back(rest, { ...card, level: LEARNING, step: 0, misses });
    }

    const step = card.step + 1;

    return step < needed ? back(rest, { ...card, step }) : rest;
}

/**
 * Ставит карточку дальше по очереди, перевернув её другой стороной: иначе слово весь
 * сеанс спрашивается одним и тем же письмом.
 */
function back<TCard extends ISessionCard>(queue: TCard[], card: TCard): TCard[] {
    const at = ahead(card.misses, queue.length);
    const turned = { ...card, isReversed: !card.isReversed };

    return [...queue.slice(0, at), turned, ...queue.slice(at)];
}

/**
 * Через сколько карточек слово вернётся: свой зазор, но не ближе порога и не дальше
 * конца очереди.
 *
 * Зазор — среднее, а не расстояние: место берётся показательным распределением. Узкий
 * разброс вокруг числа сбивает возвраты в кучу — за первым десятком новых слов идёт
 * десяток повторов подряд, — а у показательного разброс равен самому среднему, и куча
 * не собирается ни при каком размере колоды.
 */
function ahead(misses: number, length: number): number {
    const wanted =
        misses === 0
            ? GAP_AFTER_KNOW
            : GAP_AFTER_MISS[Math.min(misses, GAP_AFTER_MISS.length) - 1]!;
    const gap = Math.min(wanted, length * FURTHEST);
    const drawn = MIN_AHEAD + Math.round(-gap * Math.log(1 - Math.random()));

    return Math.min(Math.max(drawn, MIN_AHEAD), length);
}
