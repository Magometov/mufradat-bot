// #region Imports
// Types
import type { Ref } from 'vue';

import type { IEntry } from '../types/entry';
import type { IRunCard, ISavedRun, IUseRun } from '../types/run';

// Utils
import { shuffle } from '../utils/shuffle';
import { clearRun, readRun, writeRun } from '../utils/storage';

// Vue
import { computed, ref, watch } from 'vue';
// #endregion

/**
 * Прогон по колоде: перемешанный список id и место в нём.
 *
 * Порядок задаёт приложение, а не сервер: тогда «перемешать заново» и смена фильтра
 * обходятся без запроса. Колода приходит один раз, прогон — снимок с неё.
 */
export function useRun(entries: Ref<IEntry[]>): IUseRun {
    const run = ref<ISavedRun | null>(null);

    // Прогон хранит номер и направление — запись колоды подбирается здесь.
    const byId = computed<Map<string, IEntry>>(
        () => new Map(entries.value.map((entry) => [entry.id, entry])),
    );

    const cards = computed<IRunCard[]>(() => {
        if (run.value === null) return [];

        return run.value.items
            .map((item) => {
                const entry = byId.value.get(item.id);

                return entry === undefined ? null : { entry, isReversed: item.isReversed };
            })
            .filter((card): card is IRunCard => card !== null);
    });

    const total = computed<number>(() => cards.value.length);
    const index = computed<number>(() => run.value?.index ?? 0);
    const card = computed<IRunCard | null>(() => cards.value[index.value] ?? null);
    const position = computed<number>(() => index.value + 1);
    const hasPrev = computed<boolean>(() => index.value > 0);
    const hasNext = computed<boolean>(() => index.value < total.value - 1);

    /**
     * Поднимает незакрытый прогон после загрузки колоды.
     *
     * Удалённые из колоды карточки выбрасываются, индекс подрезается по остатку:
     * иначе прогон встанет на пустое место.
     */
    function restore(): void {
        const saved = readRun();
        if (saved === null) return;

        const items = saved.items.filter((item) => byId.value.has(item.id));

        if (items.length === 0) {
            clearRun();
            return;
        }

        run.value = {
            items,
            index: Math.min(Math.max(saved.index, 0), items.length - 1),
        };
    }

    /**
     * Начинает прогон по переданным карточкам — всей колоде или одной теме.
     *
     * Что отобрать, решает вызывающий: прогон помнит только номера карточек, поэтому
     * восстановление после перезагрузки не зависит от того, какой кнопкой он начат.
     *
     * Направление каждой карточки бросается монеткой и запоминается вместе с номером:
     * иначе после перезагрузки та же карточка пришла бы другой стороной вперёд.
     */
    function start(selected: IEntry[]): void {
        const items = selected.map((entry) => ({
            id: entry.id,
            isReversed: Math.random() < 0.5,
        }));

        run.value = { items: shuffle(items), index: 0 };
    }

    /**
     * Следующая карточка. На последней ничего не делает — конец прогона закрывает
     * «Готово», а не «Далее».
     */
    function next(): void {
        if (run.value === null || !hasNext.value) return;

        run.value = { ...run.value, index: run.value.index + 1 };
    }

    /**
     * Предыдущая карточка.
     */
    function prev(): void {
        if (run.value === null || !hasPrev.value) return;

        run.value = { ...run.value, index: run.value.index - 1 };
    }

    /**
     * Забывает прогон и возвращает на начальный экран.
     */
    function finish(): void {
        run.value = null;
    }

    // Пишем после каждого шага: свёрнутое окно должно открыться на той же карточке.
    watch(run, (value) => (value === null ? clearRun() : writeRun(value)));

    return { card, position, total, hasPrev, hasNext, restore, start, next, prev, finish };
}
