// #region Imports
// Types
import type { ISessionCard, TVerdict } from '../types/progress';
// #endregion

// Через сколько других карточек возвращается забытая: с каждым промахом дальше. Первый
// возврат близко, чтобы слово не успело выветриться; дальше — иначе в длинном сеансе одно
// и то же слово лезет в лицо каждые три карточки.
export const RETURN_STEPS = [5, 10, 20];

const LEARNING = 0;

/**
 * Очередь сеанса после оценки первой карточки.
 *
 * Закрытая карточка из очереди уходит, забытая возвращается тем дальше, чем чаще не
 * давалась. Уровень и счёт здесь считаются только чтобы решить, закрылась ли карточка;
 * настоящие уровень и срок пишет сервер.
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

    // Узнал с первого взгляда — карточка знакомая и уходит сразу, как и на сервере.
    if (card.level === null) return rest;

    // Знакомая карточка закрывается с первого верного ответа, изучение — со второго.
    if (card.level !== LEARNING) return rest;

    const step = card.step + 1;

    return step < needed ? back(rest, { ...card, step }) : rest;
}

/**
 * Ставит карточку дальше по очереди или в конец, если та короче нужного шага.
 *
 * Шаг берётся по числу уже случившихся промахов: первый возврат — первый шаг.
 */
function back<TCard extends ISessionCard>(queue: TCard[], card: TCard): TCard[] {
    const index = Math.min(Math.max(card.misses - 1, 0), RETURN_STEPS.length - 1);
    const at = Math.min(RETURN_STEPS[index], queue.length);

    return [...queue.slice(0, at), card, ...queue.slice(at)];
}
