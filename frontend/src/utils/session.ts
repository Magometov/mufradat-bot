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
export function answer(queue: ISessionCard[], verdict: TVerdict, needed: number): ISessionCard[] {
    const [card, ...rest] = queue;

    if (card === undefined) return [];

    if (verdict === 'forgot') return back(rest, { ...card, level: LEARNING, step: 0 });

    // Знакомая карточка закрывается с первого верного ответа, изучение — со второго.
    if (card.level !== LEARNING) return rest;

    const step = card.step + 1;

    return step < needed ? back(rest, { ...card, step }) : rest;
}

/**
 * Ставит карточку в очередь через `RETURN_AFTER` других или в конец, если их меньше.
 */
function back(queue: ISessionCard[], card: ISessionCard): ISessionCard[] {
    const at = Math.min(RETURN_AFTER, queue.length);

    return [...queue.slice(0, at), card, ...queue.slice(at)];
}
