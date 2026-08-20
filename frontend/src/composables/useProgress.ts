// #region Imports
// Types
import type {
    IAnswer,
    IProgress,
    IRules,
    IServerState,
    IUseProgress,
    TVerdict,
} from '../types/progress';

// Utils
import { API_URL } from '../utils/api';
import { isTimeToSend, pauseFor, replay } from '../utils/outbox';
import { readAnswers, writeAnswers } from '../utils/storage';

// Vue
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
// #endregion

const STATE_URL = `${API_URL}/api/v1/state/`;
const ANSWERS_URL = `${API_URL}/api/v1/answers/`;
const INIT_DATA_HEADER = 'X-Init-Data';

// Длина пачки на случай, когда правила ещё не приехали: обычно предел берётся из них.
const ANSWERS_BATCH = 100;

// Как часто очередь проверяет, не пора ли ей уехать. Сама проверка в сеть не ходит —
// решает `isTimeToSend`.
const TICK = 5000;

// Дольше запрос не ждёт: подвисший `fetch` иначе запер бы отправку до перезагрузки.
const TIMEOUT = 15_000;

/**
 * Прогресс человека: правила с сервера, очередь оценок и её отправка.
 *
 * Оценки уезжают пачками, а не по одной: пока оценка в очереди, её можно снять, и
 * поэтому отмена промаха не стоит ни запроса, ни серверной ручки.
 */
export function useProgress(initData: string): IUseProgress {
    const enabled = ref(false);
    const rules = ref<IRules | null>(null);
    // Что известно серверу. Показывать это как есть нельзя: пока очередь не уехала, он
    // не знает про последние оценки.
    const server = ref<Map<string, IProgress>>(new Map());
    const queue = ref<IAnswer[]>(readAnswers());

    // Разница между часами сервера и устройства: сроки считаются по серверным.
    let shift = 0;
    // Когда нажали в последний раз: по тишине после нажатия очередь и уезжает.
    let pressedAt = 0;
    // До этого времени ручку не трогаем: она просила подождать.
    let mutedUntil = 0;
    // Сколько оценок из головы очереди сейчас в пути: их уже не снять.
    let inFlight = 0;
    let timer = 0;
    let sending: Promise<void> | null = null;

    // Состояния сервера плюс всё, что ещё не уехало. Иначе застрявшая очередь
    // возвращает в сеанс карточки, которые человек уже закрыл.
    const progress = computed<Map<string, IProgress>>(() =>
        replay(server.value, queue.value, rules.value),
    );

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
     * Складывает состояния карточек в карту сервера по номерам.
     */
    function collect(cards: IServerState[]): void {
        const fresh = new Map(server.value);

        cards.forEach((card) => {
            fresh.set(card.id, {
                level: card.level,
                step: card.step,
                lapses: card.lapses,
                lapsedFrom: card.lapsed_from,
                dueAt: Date.parse(card.due_at),
            });
        });

        server.value = fresh;
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
                firstSightLevel: body.first_sight_level,
                needed: body.needed,
                lapseDrop: body.lapse_drop,
                answersLimit: body.answers_limit,
            };
            server.value = new Map();
            collect(body.cards);
        } catch {
            // Прогресс не доехал: колода откроется без цифр и без оценок.
        }
    }

    /**
     * Кладёт оценку в очередь и отдаёт срок, который карточку ждёт.
     */
    function record(id: string, verdict: TVerdict): IProgress | null {
        if (rules.value === null) return null;

        pressedAt = Date.now();
        queue.value = [
            ...queue.value,
            { card_id: id, verdict, answered_at: new Date(now()).toISOString() },
        ];
        writeAnswers(queue.value);

        return progress.value.get(id) ?? null;
    }

    /**
     * Снимает последнюю оценку, пока она не уехала.
     */
    function cancelLast(): boolean {
        // Оценка уже в пути — снимать поздно: сервер её применит.
        if (queue.value.length <= inFlight) return false;

        queue.value = queue.value.slice(0, -1);
        writeAnswers(queue.value);

        return true;
    }

    /**
     * Отправляет очередь целиком: конец сеанса и уход из окна.
     */
    async function flush(): Promise<void> {
        await deliver(true);
    }

    /**
     * Отправляет очередь, если ей пора: набралась пачка или человек перестал отвечать.
     */
    function flushIfReady(): void {
        void deliver(false);
    }

    /**
     * Одна отправка за раз: пока пачка в пути, вторую не начинаем.
     */
    async function deliver(all: boolean): Promise<void> {
        if (queue.value.length === 0 || sending !== null) return;
        if (Date.now() < mutedUntil) return;
        if (!all && !isReady()) return;

        sending = drain(all);

        try {
            await sending;
        } finally {
            sending = null;
        }
    }

    /**
     * Сколько оценок ручка берёт за раз. Правила ещё не приехали — своё число.
     */
    function batchSize(): number {
        return rules.value?.answersLimit ?? ANSWERS_BATCH;
    }

    /**
     * Пора ли очереди уезжать самой.
     */
    function isReady(): boolean {
        return isTimeToSend(queue.value.length, batchSize(), Date.now() - pressedAt);
    }

    /**
     * Пачка за пачкой, пока очередь не кончится или пока пачка не застрянет.
     *
     * Целиком отправлять нельзя: очередь длиннее серверного предела не уехала бы никогда.
     * Хвост короче пачки ждёт своего часа — иначе на каждой сотне уходило бы два запроса.
     */
    async function drain(all: boolean): Promise<void> {
        while (queue.value.length > 0) {
            if (!all && !isReady()) return;
            if (!(await send(queue.value.slice(0, batchSize())))) return;
        }
    }

    /**
     * Одна попытка отправки: успех убирает уехавшее из очереди. `false` — не уехало.
     */
    async function send(answers: IAnswer[]): Promise<boolean> {
        inFlight = answers.length;

        try {
            const response = await fetch(ANSWERS_URL, {
                method: 'POST',
                headers: { ...headers(), 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers }),
                // Старому webview `timeout` неизвестен: там запрос уедет без срока.
                signal: AbortSignal.timeout?.(TIMEOUT),
            });

            // Подпись не годится: в этом заходе слать некуда. Оценки при этом остаются —
            // следующий заход придёт со свежей подписью и увезёт их.
            if (response.status === 403) {
                enabled.value = false;
                mutedUntil = Number.POSITIVE_INFINITY;

                return false;
            }

            // Слишком часто: ждём, сколько просят, а не стучимся каждый тик.
            if (response.status === 429) {
                mutedUntil = Date.now() + pauseFor(response.headers.get('Retry-After'));

                return false;
            }

            if (!response.ok) return false;

            queue.value = queue.value.slice(answers.length);
            writeAnswers(queue.value);
            collect(await response.json());

            return true;
        } catch {
            // Связи нет или запрос завис: очередь остаётся, уедет со следующей попыткой.
            return false;
        } finally {
            inFlight = 0;
        }
    }

    /**
     * Отправляет очередь, когда окно прячут: там уже не до пачек.
     */
    function onHidden(): void {
        if (document.visibilityState === 'visible') return;

        void flush();
    }

    /**
     * То же при закрытии окна: `visibilitychange` в этот момент срабатывает не везде.
     */
    function onLeave(): void {
        void flush();
    }

    onMounted(() => {
        timer = window.setInterval(flushIfReady, TICK);
        window.addEventListener('pagehide', onLeave);
        document.addEventListener('visibilitychange', onHidden);
    });

    onBeforeUnmount(() => {
        window.clearInterval(timer);
        window.removeEventListener('pagehide', onLeave);
        document.removeEventListener('visibilitychange', onHidden);
    });

    return { enabled, rules, progress, now, fetchState, record, cancelLast, flush };
}
