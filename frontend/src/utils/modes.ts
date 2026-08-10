// #region Imports
// Types
import type { TRunMode } from '../types/selection';
// #endregion

/** Подписи режимов: кнопки первого экрана и заголовок второго берут их отсюда. */
export const MODE_TITLES: Record<TRunMode, string> = {
    words: 'Только слова',
    all: 'Слова и фразы',
} as const;
