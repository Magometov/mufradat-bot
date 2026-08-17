// #region Imports
// Types
import type { Ref } from 'vue';

import type { IEntry } from '../types/entry';
import type { IProgress, TVerdict } from '../types/progress';
import type { IRunCard } from '../types/run';
import type { ISessionItem, IUseSession } from '../types/session';

// Utils
import { preload } from '../utils/preload';
import { answer as move } from '../utils/session';
import { shuffle } from '../utils/shuffle';

// Vue
import { computed, ref, watch } from 'vue';
// #endregion

// Насколько вперёд тянутся картинки: столько же, сколько в просмотре колоды.
const AHEAD = 2;

/**
 * Сеанс повторения: очередь карточек и их оценка.
 *
 * Сеанс не сохраняется между заходами: закрытые карточки уже уехали на сервер, а
 * незакрытые остались просроченными — значит порция пересоберётся сама и будет вернее
 * сохранённой.
 */
export function useSession(entries: Ref<IEntry[]>, needed: Ref<number>): IUseSession {
    const queue = ref<ISessionItem[]>([]);
    const total = ref(0);
    // Очередь до последней оценки: отмена в тосте возвращает её целиком.
    let before: ISessionItem[] | null = null;

    const byId = computed<Map<string, IEntry>>(
        () => new Map(entries.value.map((entry) => [entry.id, entry])),
    );

    const card = computed<IRunCard | null>(() => {
        const first = queue.value[0];
        const entry = first === undefined ? undefined : byId.value.get(first.id);

        return entry === undefined ? null : { entry, isReversed: first!.isReversed };
    });

    const left = computed<number>(() => queue.value.length);

    const done = computed<number>(() =>
        total.value === 0 ? 0 : (total.value - queue.value.length) / total.value,
    );

    /**
     * Набирает сеанс из готовой порции: порядок перемешан, сторона брошена монеткой.
     */
    function start(portion: IEntry[], progress: Map<string, IProgress>): void {
        const items = portion.map((entry) => {
            const state = progress.get(entry.id);

            return {
                id: entry.id,
                isReversed: Math.random() < 0.5,
                level: state?.level ?? null,
                step: state?.step ?? 0,
            };
        });

        queue.value = shuffle(items);
        total.value = items.length;
        before = null;
    }

    /**
     * Оценивает первую карточку: закрытая уходит, забытая вернётся через несколько других.
     */
    function answer(verdict: TVerdict): void {
        before = queue.value;
        queue.value = move(queue.value, verdict, needed.value);
    }

    /**
     * Возвращает очередь к состоянию до последней оценки.
     */
    function undo(): void {
        if (before === null) return;

        queue.value = before;
        before = null;
    }

    /**
     * Бросает сеанс.
     */
    function finish(): void {
        queue.value = [];
        total.value = 0;
        before = null;
    }

    // Картинка лежит на обороте, то есть нужна ровно в момент переворота. Тянем её
    // заранее, пока смотрят на предыдущую: иначе ответ открывается пустой рамкой.
    watch(
        queue,
        (items) => {
            const ahead = items.slice(0, AHEAD + 1).map((item) => byId.value.get(item.id) ?? null);

            preload(ahead.map((entry) => entry?.image ?? null));
        },
        { immediate: true },
    );

    return { card, left, done, start, answer, undo, finish };
}
