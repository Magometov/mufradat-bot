// #region Imports
// Types
import type { ISessionCard, TVerdict } from '../types/progress';

// Utils
import { LEARNING } from './levels';
// #endregion

// Через сколько других карточек возвращается забытая: с каждым промахом дальше. Первый
// возврат — за полтора десятка: раньше слово ещё висит в голове, и «помню» говорится
// памятью о прошлой карточке, а не о самом слове.
export const RETURN_STEPS = [15, 30, 60];

// Сколько чужих карточек обязано лежать между двумя возвращёнными.
export const MIN_GAP = 3;

// Разброс вверх от шага: возврат перестаёт быть отсчитываемым ритмом, но ближе шага
// карточка не подходит. Тот же приём, что и у лестницы сроков на сервере.
export const SPREAD = 0.3;

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
 * Ставит карточку дальше по очереди или в конец, если та короче нужного шага.
 *
 * Шаг берётся по числу уже случившихся промахов: первый возврат — первый шаг. Сторона
 * при возврате меняется: иначе слово весь сеанс спрашивается одним и тем же письмом.
 */
function back<TCard extends ISessionCard>(queue: TCard[], card: TCard): TCard[] {
    const at = free(queue, Math.min(step(card.misses), queue.length));
    const turned = { ...card, isReversed: !card.isReversed };

    return [...queue.slice(0, at), turned, ...queue.slice(at)];
}

/**
 * Через сколько карточек возвращать: порог по числу промахов плюс разброс вверх.
 */
function step(misses: number): number {
    const index = Math.min(Math.max(misses - 1, 0), RETURN_STEPS.length - 1);
    const floor = RETURN_STEPS[index]!;

    return floor + Math.floor(Math.random() * floor * SPREAD);
}

/**
 * Ближайшее с этого место, рядом с которым нет другой возвращённой карточки.
 *
 * Без него промахи, сделанные подряд, встают на одно и то же место остатка очереди и
 * возвращаются кучей: шаг у них общий, а очередь к каждому следующему короче ровно на
 * предыдущий.
 */
function free<TCard extends ISessionCard>(queue: TCard[], at: number): number {
    let place = at;

    while (place < queue.length && crowded(queue, place)) place += 1;

    return place;
}

/**
 * Есть ли возвращённая карточка в зазоре вокруг места.
 */
function crowded<TCard extends ISessionCard>(queue: TCard[], at: number): boolean {
    return queue.slice(Math.max(at - MIN_GAP, 0), at + MIN_GAP).some((item) => item.misses > 0);
}
