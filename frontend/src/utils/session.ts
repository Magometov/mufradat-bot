// #region Imports
// Types
import type { ISessionCard, TVerdict } from '../types/progress';
// #endregion

// Через столько других карточек возвращается забытая. Меньше — и слово не успевает
// вылететь из головы, а значит припоминания не происходит.
export const RETURN_AFTER = 3;

const LEARNING = 0;

/**
 * Очередь сеанса после оценки первой карточки.
 *
 * Закрытая карточка из очереди уходит, забытая возвращается через несколько других.
 * Уровень и счёт здесь считаются только чтобы решить, закрылась ли карточка; настоящие
 * уровень и срок пишет сервер.
 */
export function answer<TCard extends ISessionCard>(
    queue: TCard[],
    verdict: TVerdict,
    needed: number,
): TCard[] {
    const [card, ...rest] = queue;

    if (card === undefined) return [];

    if (verdict === 'forgot') return back(rest, { ...card, level: LEARNING, step: 0 });

    // Узнал с первого взгляда — карточка знакомая и уходит сразу, как и на сервере.
    if (card.level === null) return rest;

    // Знакомая карточка закрывается с первого верного ответа, изучение — со второго.
    if (card.level !== LEARNING) return rest;

    const step = card.step + 1;

    return step < needed ? back(rest, { ...card, step }) : rest;
}

/**
 * Ставит карточку в очередь через `RETURN_AFTER` других или в конец, если их меньше.
 */
function back<TCard extends ISessionCard>(queue: TCard[], card: TCard): TCard[] {
    const at = Math.min(RETURN_AFTER, queue.length);

    return [...queue.slice(0, at), card, ...queue.slice(at)];
}
