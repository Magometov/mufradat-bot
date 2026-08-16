// #region Imports
// Types
import type { Ref } from 'vue';

import type { IEntry } from '../types/entry';
import type { IUseSelection, TRunMode } from '../types/selection';
import type { ITheme } from '../types/theme';

// Vue
import { computed, ref } from 'vue';
// #endregion

/**
 * Выбор перед прогоном: что повторяем и каким разделом.
 *
 * Режим лежит здесь, а не внутри экранов: на время прогона они размонтируются, и после
 * «Готово» выбор бы терялся — а один раздел обычно гоняют не по разу.
 */
export function useSelection(entries: Ref<IEntry[]>, themes: Ref<ITheme[]>): IUseSelection {
    const mode = ref<TRunMode | null>(null);

    const deck = computed<IEntry[]>(() =>
        mode.value === 'words' ? entries.value.filter((entry) => entry.is_word) : entries.value,
    );

    // Раздел без карточек дал бы кнопку в пустой прогон: в режиме слов пустых больше.
    const sections = computed<ITheme[]>(() =>
        themes.value.filter((theme) =>
            deck.value.some((entry) => entry.themes.includes(theme.slug)),
        ),
    );

    /**
     * Запоминает выбранный режим.
     */
    function choose(value: TRunMode): void {
        mode.value = value;
    }

    /**
     * Карточки для прогона: весь режим или один его раздел.
     */
    function cardsFor(theme: string | null): IEntry[] {
        if (theme === null) return deck.value;

        return deck.value.filter((entry) => entry.themes.includes(theme));
    }

    /**
     * Забывает режим — приложение возвращается на первый экран.
     */
    function reset(): void {
        mode.value = null;
    }

    return { mode, sections, choose, cardsFor, reset };
}
