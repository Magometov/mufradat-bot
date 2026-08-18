// #region Imports
// Types
import type { IProgress, IRules, TVerdict } from '../types/progress';

// Utils
import { FIRST_SCHEDULED, LEARNING } from './levels';
// #endregion

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
    if (verdict === 'forgot') {
        return { level: LEARNING, step: 0, lapsedFrom: fellFrom(current), dueAt: now };
    }

    if (current === undefined) return scheduled(rules.firstSightLevel, rules, now);

    if (current.level !== LEARNING) {
        return scheduled(Math.min(current.level + 1, rules.ladder.length), rules, now);
    }

    const step = current.step + 1;

    if (step < rules.needed) return { ...current, step, dueAt: now };

    return scheduled(relearned(current.lapsedFrom, rules), rules, now);
}

/**
 * С какой ступени карточка упала. Промах в изучении прежнее падение не стирает.
 */
function fellFrom(current: IProgress | undefined): number {
    if (current === undefined) return LEARNING;

    return current.level === LEARNING ? current.lapsedFrom : current.level;
}

/**
 * Куда возвращается переученная карточка: ниже прежней ступени, но не в самый низ.
 */
function relearned(lapsedFrom: number, rules: IRules): number {
    return Math.max(FIRST_SCHEDULED, lapsedFrom - rules.lapseDrop);
}

/**
 * Состояние карточки, уехавшей в расписание на свой уровень.
 */
function scheduled(level: number, rules: IRules, now: number): IProgress {
    // След падения потрачен: карточка снова на лестнице.
    return { level, step: 0, lapsedFrom: 0, dueAt: now + days(level, rules) * DAY };
}

/**
 * Сколько дней держится уровень. За последним уровнем — последний срок лестницы.
 */
export function days(level: number, rules: IRules): number {
    return rules.ladder[Math.min(level, rules.ladder.length) - 1] ?? 0;
}
