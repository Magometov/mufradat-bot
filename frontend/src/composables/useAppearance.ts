// #region Imports
// Types
import type { IUseAppearance, TAppearance } from '../types/appearance';

// Utils
import { readAppearance, writeAppearance } from '../utils/storage';

// Vue
import { ref } from 'vue';
// #endregion

// Светлое у всех одинаково: клиент Telegram и настройки системы тут не спрашивают.
const DEFAULT: TAppearance = 'light';

/**
 * Светлое или тёмное оформление.
 *
 * Тему уже поставил скрипт в разметке — до первой отрисовки, иначе тёмная моргала бы
 * белым при каждом запуске. Здесь только переключение и запоминание выбора.
 */
export function useAppearance(): IUseAppearance {
    const appearance = ref<TAppearance>(readAppearance() ?? DEFAULT);

    /**
     * Меняет оформление на противоположное и запоминает выбор.
     */
    function toggle(): void {
        appearance.value = appearance.value === 'dark' ? 'light' : 'dark';

        document.documentElement.dataset.theme = appearance.value;
        writeAppearance(appearance.value);
    }

    return { appearance, toggle };
}
