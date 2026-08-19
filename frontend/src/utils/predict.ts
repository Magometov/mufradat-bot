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
    // Новая карточка — это состояние по умолчанию: дальше правило одно на всех.
    const state = current ?? { level: LEARNING, step: 0, lapses: 0, lapsedFrom: 0, dueAt: now };

    if (verdict === 'forgot') return forgotten(state, now);

    const step = state.step + 1;

    // Подтверждена не всякая сторона — карточка вернётся в этом же сеансе за остальными.
    if (step < rules.needed) return { ...state, step, dueAt: now };

    const level = closedLevel(state, rules);

    // След падения потрачен: карточка снова на лестнице.
    return {
        level,
        step: 0,
        lapses: state.lapses,
        lapsedFrom: 0,
        dueAt: now + days(level, rules) * DAY,
    };
}

/**
 * Изучение с начала, но со следом падения: промах в изучении прежний след не стирает.
 */
function forgotten(state: IProgress, now: number): IProgress {
    const fellFrom = state.level === LEARNING ? state.lapsedFrom : state.level;

    return {
        level: LEARNING,
        step: 0,
        lapses: state.lapses + 1,
        lapsedFrom: fellFrom,
        dueAt: now,
    };
}

/**
 * На какую ступень встаёт карточка, подтвердившая все стороны. Выше лестницы некуда.
 *
 * Потолок общий на все ветки: ступень первого взгляда могли выкрутить за край лестницы,
 * а саму лестницу — укоротить при уже расставленных уровнях.
 */
function closedLevel(state: IProgress, rules: IRules): number {
    return Math.min(wantedLevel(state, rules), rules.ladder.length);
}

/**
 * Куда карточка метит: на следующую ступень, на ступень первого взгляда или ниже прежней.
 */
function wantedLevel(state: IProgress, rules: IRules): number {
    if (state.level !== LEARNING) return state.level + 1;

    // Ни разу не забывалась — знал заранее, а не вспомнил с третьего раза.
    if (state.lapses === 0) return rules.firstSightLevel;

    // Переученная возвращается ниже прежней ступени, но не в самый низ.
    return Math.max(FIRST_SCHEDULED, state.lapsedFrom - rules.lapseDrop);
}

/**
 * Сколько дней держится уровень. За последним уровнем — последний срок лестницы.
 */
export function days(level: number, rules: IRules): number {
    return rules.ladder[Math.min(level, rules.ladder.length) - 1] ?? 0;
}
