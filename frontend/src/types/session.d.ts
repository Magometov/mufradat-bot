import type { ComputedRef } from 'vue';

import type { IEntry } from './entry';
import type { IProgress, TVerdict } from './progress';
import type { IRunCard } from './run';

/** Карточка в очереди сеанса: номер, сторона и то, что нужно для решения о возврате. */
export interface ISessionItem {
    id: string;
    /** Русский вперёд: лицо — перевод, оборот — арабское. */
    isReversed: boolean;
    /** `null` — карточку видят впервые. */
    level: number | null;
    step: number;
    misses: number;
}

export interface IUseSession {
    card: ComputedRef<IRunCard | null>;
    /** Сколько карточек ещё не закрыто. */
    left: ComputedRef<number>;
    /** Номера карточек, с которыми сеанс начался: по ним считается итог. */
    ids: ComputedRef<string[]>;
    /** Доля пройденного для полосы прогресса. */
    done: ComputedRef<number>;
    /** Набирает сеанс из готовой порции. */
    start: (portion: IEntry[], progress: Map<string, IProgress>) => void;
    /** Оценивает первую карточку и двигает очередь. */
    answer: (verdict: TVerdict) => void;
    /** Возвращает очередь к состоянию до последней оценки. */
    undo: () => void;
    finish: () => void;
}
