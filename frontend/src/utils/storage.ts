import type { IRunItem, ISavedRun } from '../types/run';

const KEY = 'mufradat.run';

/**
 * Похожа ли запись на карточку прогона.
 */
function isRunItem(value: unknown): value is IRunItem {
    if (typeof value !== 'object' || value === null) return false;

    const candidate = value as Record<string, unknown>;

    return typeof candidate.id === 'number' && typeof candidate.isReversed === 'boolean';
}

/**
 * Похоже ли прочитанное на прогон. Всё непохожее считается его отсутствием: формат
 * менялся, когда у карточек появилось направление, и старые прогоны просто не поднимутся.
 */
function isSavedRun(value: unknown): value is ISavedRun {
    if (typeof value !== 'object' || value === null) return false;

    const candidate = value as Record<string, unknown>;

    return (
        Array.isArray(candidate.items) &&
        candidate.items.every(isRunItem) &&
        typeof candidate.index === 'number'
    );
}

/**
 * Читает незакрытый прогон. `null`, если его нет или он нечитаем.
 */
export function readRun(): ISavedRun | null {
    try {
        const raw = localStorage.getItem(KEY);
        if (raw === null) return null;

        const parsed: unknown = JSON.parse(raw);

        return isSavedRun(parsed) ? parsed : null;
    } catch {
        // Приватный режим и битый JSON лечатся одинаково — прогона просто нет.
        return null;
    }
}

/**
 * Запоминает прогон, чтобы свёрнутое окно не теряло место в колоде.
 */
export function writeRun(run: ISavedRun): void {
    try {
        localStorage.setItem(KEY, JSON.stringify(run));
    } catch {
        // Без записи прогон живёт до перезагрузки — это лучше, чем падение.
    }
}

/**
 * Забывает прогон: «Завершить» и конец колоды.
 */
export function clearRun(): void {
    try {
        localStorage.removeItem(KEY);
    } catch {
        // Нечего чистить.
    }
}
