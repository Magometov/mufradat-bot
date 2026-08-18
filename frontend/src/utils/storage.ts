import type { TAppearance } from '../types/appearance';
import type { IAnswer } from '../types/progress';
import type { IRunItem, ISavedRun } from '../types/run';

// Номер в ключе — версия формата. Карточки переехали в две таблицы и сменили номера
// с чисел на строки: старый прогон не упал бы, а молча подставил чужие карточки.
const RUN_KEY = 'mufradat.run.2';

// Оценки, ещё не уехавшие на сервер. Номер в ключе — версия формата: у оценки появилось
// время нажатия, и без него сервер её не примет.
const ANSWERS_KEY = 'mufradat.answers.2';

// Показывали ли подсказки про расписание.
const TIPS_KEY = 'mufradat.tips.1';

// Эти два ключа продублированы в index.html: оформление там читают до первой
// отрисовки, когда приложения ещё нет. Меняешь здесь — правь и там.
const APPEARANCE_KEY = 'mufradat.appearance';
const HINT_KEY = 'mufradat.appearance.hint';

/**
 * Похожа ли запись на карточку прогона.
 */
function isRunItem(value: unknown): value is IRunItem {
    if (typeof value !== 'object' || value === null) return false;

    const candidate = value as Record<string, unknown>;

    return typeof candidate.id === 'string' && typeof candidate.isReversed === 'boolean';
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
        const raw = localStorage.getItem(RUN_KEY);
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
        localStorage.setItem(RUN_KEY, JSON.stringify(run));
    } catch {
        // Без записи прогон живёт до перезагрузки — это лучше, чем падение.
    }
}

/**
 * Забывает прогон: «Завершить» и конец колоды.
 */
export function clearRun(): void {
    try {
        localStorage.removeItem(RUN_KEY);
    } catch {
        // Нечего чистить.
    }
}

/**
 * Выбранное оформление. `null` — человек ещё не выбирал, значит светлое.
 */
export function readAppearance(): TAppearance | null {
    try {
        const raw = localStorage.getItem(APPEARANCE_KEY);

        return raw === 'light' || raw === 'dark' ? raw : null;
    } catch {
        // Приватный режим: оформление будет светлым до конца сеанса.
        return null;
    }
}

/**
 * Запоминает выбор оформления.
 */
export function writeAppearance(appearance: TAppearance): void {
    try {
        localStorage.setItem(APPEARANCE_KEY, appearance);
    } catch {
        // Без записи выбор живёт до перезагрузки — это лучше, чем падение.
    }
}

/**
 * Показывали ли уже подсказку про кнопку оформления.
 */
export function isHintSeen(): boolean {
    try {
        return localStorage.getItem(HINT_KEY) !== null;
    } catch {
        // Не знаем — считаем, что показывали: лишний раз навязываться хуже.
        return true;
    }
}

/**
 * Отмечает подсказку показанной.
 */
export function markHintSeen(): void {
    try {
        localStorage.setItem(HINT_KEY, '1');
    } catch {
        // Тогда она покажется ещё раз в следующий заход. Не беда.
    }
}

/**
 * Похожа ли запись на оценку.
 */
function isAnswer(value: unknown): value is IAnswer {
    if (typeof value !== 'object' || value === null) return false;

    const candidate = value as Record<string, unknown>;

    return (
        typeof candidate.card_id === 'string' &&
        typeof candidate.answered_at === 'string' &&
        (candidate.verdict === 'know' || candidate.verdict === 'forgot')
    );
}

/**
 * Читает оценки, ждущие отправки. Нечитаемое считается пустой очередью.
 */
export function readAnswers(): IAnswer[] {
    try {
        const raw = localStorage.getItem(ANSWERS_KEY);
        if (raw === null) return [];

        const parsed: unknown = JSON.parse(raw);

        return Array.isArray(parsed) && parsed.every(isAnswer) ? parsed : [];
    } catch {
        // Приватный режим и битый JSON лечатся одинаково — очереди просто нет.
        return [];
    }
}

/**
 * Запоминает очередь оценок: закрытое окно не должно уносить их с собой.
 */
export function writeAnswers(answers: IAnswer[]): void {
    try {
        if (answers.length === 0) {
            localStorage.removeItem(ANSWERS_KEY);
            return;
        }

        localStorage.setItem(ANSWERS_KEY, JSON.stringify(answers));
    } catch {
        // Без записи оценки живут до перезагрузки — это лучше, чем падение.
    }
}

/**
 * Видели ли подсказки. Не знаем — считаем, что видели: навязываться лишний раз хуже.
 */
export function isTipsSeen(): boolean {
    try {
        return localStorage.getItem(TIPS_KEY) !== null;
    } catch {
        return true;
    }
}

/**
 * Отмечает подсказки показанными.
 */
export function markTipsSeen(): void {
    try {
        localStorage.setItem(TIPS_KEY, '1');
    } catch {
        // Тогда они покажутся ещё раз в следующий заход. Не беда.
    }
}
