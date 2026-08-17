// #region Imports
// Types
import type { IEntry } from '../types/entry';
import type { IProgress } from '../types/progress';

// Utils
import { dayWord, wordWord } from './plural';
// #endregion

const DAY = 86_400_000;

/**
 * Сколько карточек назначено на сегодня: изучение, просроченные и ни разу не виденные.
 */
export function countDue(entries: IEntry[], progress: Map<string, IProgress>, now: number): number {
    return entries.filter((entry) => {
        const state = progress.get(entry.id);

        return state === undefined || state.dueAt <= now;
    }).length;
}

/**
 * Когда придёт ближайшая карточка. `null` — расписание пусто.
 */
export function nextDueAt(entries: IEntry[], progress: Map<string, IProgress>): number | null {
    const dates = entries
        .map((entry) => progress.get(entry.id)?.dueAt)
        .filter((dueAt): dueAt is number => dueAt !== undefined);

    return dates.length === 0 ? null : Math.min(...dates);
}

/**
 * Когда это будет, словами: «завтра», «через 4 дня». Дни считаются по календарю, а не
 * по разнице в сутках, иначе «завтра утром» превращается в «сегодня».
 */
export function soonText(dueAt: number, now: number): string {
    const days = Math.round((midnight(dueAt) - midnight(now)) / DAY);

    if (days <= 0) return 'сегодня';
    if (days === 1) return 'завтра';
    if (days === 2) return 'послезавтра';

    return `через ${days} ${dayWord(days)}`;
}

/**
 * Начало суток указанного момента.
 */
function midnight(at: number): number {
    const date = new Date(at);

    date.setHours(0, 0, 0, 0);

    return date.getTime();
}

/**
 * Итог сеанса словами: «8 слов вернутся через неделю, 2 — завтра».
 *
 * Группы идут по возрастанию срока, поэтому первым читается самое далёкое обещание.
 */
export function summarize(ids: string[], progress: Map<string, IProgress>, now: number): string {
    const groups = new Map<string, { count: number; dueAt: number }>();

    ids.forEach((id) => {
        const state = progress.get(id);
        if (state === undefined) return;

        const text = soonText(state.dueAt, now);
        const group = groups.get(text);

        if (group === undefined) groups.set(text, { count: 1, dueAt: state.dueAt });
        else group.count += 1;
    });

    const parts = [...groups.entries()]
        .sort((first, second) => second[1].dueAt - first[1].dueAt)
        .map(([text, group], index) => {
            if (index > 0) return `${group.count} — ${text}`;

            const verb = group.count === 1 ? 'вернётся' : 'вернутся';

            return `${group.count} ${wordWord(group.count)} ${verb} ${text}`;
        });

    return parts.length === 0 ? 'Оценок в этом сеансе не было.' : `${parts.join(', ')}.`;
}
