// #region Imports
// Types
import type { IProgress, IRules, TVerdict } from '../types/progress';
// #endregion

const LEARNING = 0;
const DAY = 86_400_000;

/**
 * Каким станет состояние карточки после оценки.
 *
 * Повторяет правило сервера, но без разброса: нужно только чтобы показать в тосте
 * «через 7 дней» и собрать следующую порцию до того, как пачка уехала. Настоящий срок
 * с разбросом пишет сервер, и его ответ эти догадки заменяет.
 */
export function predict(
    current: IProgress | undefined,
    verdict: TVerdict,
    rules: IRules,
    now: number,
): IProgress {
    if (verdict === 'forgot') return { level: LEARNING, step: 0, dueAt: now };

    if (current === undefined) return scheduled(rules.firstSightLevel, rules, now);

    if (current.level !== LEARNING) {
        return scheduled(Math.min(current.level + 1, rules.ladder.length), rules, now);
    }

    const step = current.step + 1;

    return step < rules.needed ? { level: LEARNING, step, dueAt: now } : scheduled(1, rules, now);
}

/**
 * Состояние карточки, уехавшей в расписание на свой уровень.
 */
function scheduled(level: number, rules: IRules, now: number): IProgress {
    return { level, step: 0, dueAt: now + days(level, rules) * DAY };
}

/**
 * Сколько дней держится уровень. За последним уровнем — последний срок лестницы.
 */
export function days(level: number, rules: IRules): number {
    return rules.ladder[Math.min(level, rules.ladder.length) - 1] ?? 0;
}
