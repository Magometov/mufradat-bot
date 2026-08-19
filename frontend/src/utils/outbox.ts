// #region Imports
// Types
import type { IAnswer, IProgress, IRules } from '../types/progress';

// Utils
import { predict } from './predict';
// #endregion

// Столько тишины после нажатия считается «человек отвлёкся или закончил»: очередь
// уезжает, не дожидаясь полной пачки.
export const IDLE_PAUSE = 15_000;

// Сколько молчать после отказа «слишком часто», если ручка не сказала сколько.
export const PAUSE_DEFAULT = 60_000;

// Дольше не молчим ни по какой просьбе: очередь должна уехать в этом же заходе.
export const PAUSE_LONGEST = 600_000;

/**
 * Прогресс, каким его видит человек: состояния сервера и оценки, что ещё не уехали.
 *
 * Без этого сеанс собирается по одному серверу, и карточка, чья оценка застряла в
 * очереди, приходит снова — хотя человек её уже закрыл.
 */
export function replay(
    server: Map<string, IProgress>,
    answers: IAnswer[],
    rules: IRules | null,
): Map<string, IProgress> {
    if (rules === null || answers.length === 0) return server;

    const fresh = new Map(server);

    answers.forEach((answer) => {
        const pressed = Date.parse(answer.answered_at);

        // Время нечитаемо — оценка досталась от битой записи в браузере. Считать по ней
        // срок нельзя: `NaN` спрятал бы карточку из расписания навсегда.
        if (Number.isNaN(pressed)) return;

        fresh.set(
            answer.card_id,
            predict(fresh.get(answer.card_id), answer.verdict, rules, pressed),
        );
    });

    return fresh;
}

/**
 * Пора ли очереди уезжать самой.
 *
 * Ручка считает запросы, а не оценки, поэтому запрос на каждое нажатие съедал бы её
 * предел за четверть часа, и остаток сеанса не доехал бы вовсе. Ждём полной пачки или
 * паузы в ответах: длинный сеанс укладывается в десяток запросов вместо сотен.
 */
export function isTimeToSend(pending: number, limit: number, quietFor: number): boolean {
    if (pending === 0) return false;

    return pending >= limit || quietFor >= IDLE_PAUSE;
}

/**
 * Сколько молчать после отказа «слишком часто». Просьбу читаем, но не безоговорочно.
 */
export function pauseFor(retryAfter: string | null): number {
    const seconds = Number(retryAfter);

    if (!Number.isFinite(seconds) || seconds <= 0) return PAUSE_DEFAULT;

    return Math.min(seconds * 1000, PAUSE_LONGEST);
}
