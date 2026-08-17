// #region Imports
// Types
import type { IAnswer, IProgress, IRules, IUseProgress, TVerdict } from '../types/progress';

// Utils
import { API_URL } from '../utils/api';
import { predict } from '../utils/predict';
import { readAnswers, writeAnswers } from '../utils/storage';

// Vue
import { onBeforeUnmount, onMounted, ref } from 'vue';
// #endregion

const STATE_URL = `${API_URL}/api/v1/state/`;
const ANSWERS_URL = `${API_URL}/api/v1/answers/`;
const INIT_DATA_HEADER = 'X-Init-Data';

// Как часто очередь пробует уехать. Реже — и оценки дольше висят в браузере; чаще — и
// отменять промах становится некогда.
const FLUSH_EVERY = 8000;

/**
 * Прогресс человека: правила с сервера, очередь оценок и её отправка.
 *
 * Оценки уезжают пачками, а не по одной: пока оценка в очереди, её можно снять, и
 * поэтому отмена промаха не стоит ни запроса, ни серверной ручки.
 */
export function useProgress(initData: string): IUseProgress {
    const enabled = ref(false);
    const rules = ref<IRules | null>(null);
    const progress = ref<Map<string, IProgress>>(new Map());
    const queue = ref<IAnswer[]>(readAnswers());

    // Разница между часами сервера и устройства: сроки считаются по серверным.
    let shift = 0;
    // Что было до последней оценки — для отмены в тосте.
    let before: { id: string; state: IProgress | undefined } | null = null;
    let timer = 0;
    let sending: Promise<void> | null = null;

    /**
     * Время сервера по нашим часам.
     */
    function now(): number {
        return Date.now() + shift;
    }

    /**
     * Заголовки запроса: подпись Telegram, если приложение открыто в клиенте.
     */
    function headers(): HeadersInit {
        return initData === '' ? {} : { [INIT_DATA_HEADER]: initData };
    }

    /**
     * Складывает состояния карточек в карту по номерам.
     */
    function collect(cards: { id: string; level: number; step: number; due_at: string }[]): void {
        const fresh = new Map(progress.value);

        cards.forEach((card) => {
            fresh.set(card.id, {
                level: card.level,
                step: card.step,
                dueAt: Date.parse(card.due_at),
            });
        });

        progress.value = fresh;
    }

    /**
     * Забирает правила и прогресс. Не доехало — приложение работает как без него.
     */
    async function fetchState(): Promise<void> {
        try {
            const response = await fetch(STATE_URL, { headers: headers() });
            if (!response.ok) return;

            const body = await response.json();

            shift = Date.parse(body.now) - Date.now();
            enabled.value = body.enabled;
            rules.value = {
                ladder: body.ladder,
                jitter: body.jitter,
                sessionLimit: body.session_limit,
                newLimit: body.new_limit,
                firstSightLevel: body.first_sight_level,
                needed: body.needed,
            };
            progress.value = new Map();
            collect(body.cards);
        } catch {
            // Прогресс не доехал: колода откроется без цифр и без оценок.
        }
    }

    /**
     * Кладёт оценку в очередь и сразу считает, куда карточка уедет.
     */
    function record(id: string, verdict: TVerdict): IProgress | null {
        if (rules.value === null) return null;

        const state = predict(progress.value.get(id), verdict, rules.value, now());

        before = { id, state: progress.value.get(id) };
        queue.value = [...queue.value, { card_id: id, verdict }];
        writeAnswers(queue.value);

        const fresh = new Map(progress.value);
        fresh.set(id, state);
        progress.value = fresh;

        return state;
    }

    /**
     * Снимает последнюю оценку, пока она не уехала.
     */
    function cancelLast(): boolean {
        if (before === null || queue.value.length === 0) return false;

        queue.value = queue.value.slice(0, -1);
        writeAnswers(queue.value);

        const fresh = new Map(progress.value);

        if (before.state === undefined) fresh.delete(before.id);
        else fresh.set(before.id, before.state);

        progress.value = fresh;
        before = null;

        return true;
    }

    /**
     * Отправляет очередь пачкой. Не дошло — оценки остаются ждать следующего раза.
     */
    async function flush(): Promise<void> {
        if (queue.value.length === 0 || sending !== null) return;

        const sent = queue.value;
        sending = send(sent);

        try {
            await sending;
        } finally {
            sending = null;
        }
    }

    /**
     * Одна попытка отправки: успех очищает очередь от уехавшего.
     */
    async function send(answers: IAnswer[]): Promise<void> {
        try {
            const response = await fetch(ANSWERS_URL, {
                method: 'POST',
                headers: { ...headers(), 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers }),
            });

            // Оценки нас не касаются: писать их некуда, и повторять попытки незачем.
            if (response.status === 403) {
                enabled.value = false;
                queue.value = [];
                writeAnswers(queue.value);

                return;
            }

            if (!response.ok) return;

            queue.value = queue.value.slice(answers.length);
            writeAnswers(queue.value);
            before = null;
            collect(await response.json());
        } catch {
            // Связи нет: очередь остаётся, уедет со следующей попыткой.
        }
    }

    /**
     * Отправляет очередь, когда окно закрывают или прячут.
     */
    function onHide(): void {
        void flush();
    }

    onMounted(() => {
        timer = window.setInterval(() => void flush(), FLUSH_EVERY);
        window.addEventListener('pagehide', onHide);
        document.addEventListener('visibilitychange', onHide);
    });

    onBeforeUnmount(() => {
        window.clearInterval(timer);
        window.removeEventListener('pagehide', onHide);
        document.removeEventListener('visibilitychange', onHide);
    });

    return { enabled, rules, progress, now, fetchState, record, cancelLast, flush };
}
