// #region Imports
// Types
import type { IEntry } from '../types/entry';
import type { ILimits, IProgress } from '../types/progress';
// #endregion

// Уровень изучения: срок «сейчас», поэтому такие карточки идут первыми.
const LEARNING = 0;

/**
 * Что попадает в сеанс: сначала изучение, потом просроченные, потом новые.
 *
 * Порядок очередей и есть правило «долг не растёт быстрее, чем его гасят»: новые
 * карточки берутся только на места, оставшиеся после возвратов.
 */
export function buildPortion(
    entries: IEntry[],
    progress: Map<string, IProgress>,
    now: number,
    limits: ILimits | null,
): IEntry[] {
    const learning: IEntry[] = [];
    const due: IEntry[] = [];
    const fresh: IEntry[] = [];

    entries.forEach((entry) => {
        const state = progress.get(entry.id);

        if (state === undefined) {
            fresh.push(entry);
            return;
        }

        if (state.level === LEARNING) {
            learning.push(entry);
            return;
        }

        if (state.dueAt <= now) due.push(entry);
    });

    const byDue = (first: IEntry, second: IEntry): number =>
        (progress.get(first.id)?.dueAt ?? 0) - (progress.get(second.id)?.dueAt ?? 0);

    learning.sort(byDue);
    due.sort(byDue);

    if (limits === null) return [...learning, ...due, ...fresh];

    const repeats = [...learning, ...due].slice(0, limits.sessionLimit);
    const room = Math.min(limits.sessionLimit - repeats.length, limits.newLimit);

    return [...repeats, ...fresh.slice(0, Math.max(room, 0))];
}
