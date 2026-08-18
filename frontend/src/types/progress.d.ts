import type { Ref } from 'vue';

/** Состояние карточки, каким его отдаёт сервер: имена полей его, время строкой. */
export interface IServerState {
    id: string;
    level: number;
    step: number;
    lapsed_from: number;
    due_at: string;
}

/** Что человек помнит про одну карточку. Приходит из `GET /api/v1/state/`. */
export interface IProgress {
    level: number;
    /** Верных ответов подряд в изучении: 0 или 1. */
    step: number;
    /** Ступень, с которой карточка упала: на неё же и вернётся, только ниже. */
    lapsedFrom: number;
    /** Срок показа в миллисекундах — сравнивать дешевле, чем строки. */
    dueAt: number;
}

/** Правила расписания. Считает по ним приложение, задаёт их сервер. */
export interface IRules {
    ladder: number[];
    jitter: number;
    /** Потолок сеанса у кнопки «Повторить»; в разделе потолка нет. */
    sessionLimit: number;
    newLimit: number;
    firstSightLevel: number;
    /** Столько верных ответов подряд закрывает изучение. */
    needed: number;
    /** На столько ступеней опускается забытая карточка. */
    lapseDrop: number;
    /** Сколько оценок ручка принимает за раз: очередь уезжает пачками по столько. */
    answersLimit: number;
}

/** Ответ ручки состояния целиком. */
export interface IState {
    enabled: boolean;
    /** Время сервера: часы телефона врут, а сроки считаются по нему. */
    now: number;
    rules: IRules;
    progress: Map<string, IProgress>;
}

/** Потолки набора. `null` — заход в раздел, там их нет. */
export interface ILimits {
    sessionLimit: number;
    newLimit: number;
}

/** Карточка в очереди сеанса: сторона и то, что нужно для решения о возврате. */
export interface ISessionCard {
    id: string;
    /** Русский вперёд: лицо — перевод, оборот — арабское. */
    isReversed: boolean;
    /** `null` — карточку видят впервые: у неё ещё нет уровня. */
    level: number | null;
    step: number;
    /** Сколько раз слово не вспомнилось в этом сеансе: от этого зависит возврат. */
    misses: number;
}

/** Что человек сказал про карточку. */
export type TVerdict = 'know' | 'forgot';

/** Оценка, ждущая отправки. */
export interface IAnswer {
    card_id: string;
    verdict: TVerdict;
    /** Когда нажали, по часам сервера: от него считается срок. */
    answered_at: string;
}

/** Что вернул `useProgress`. */
export interface IUseProgress {
    /** Видит ли человек новую логику. */
    enabled: Ref<boolean>;
    rules: Ref<IRules | null>;
    progress: Ref<Map<string, IProgress>>;
    /** Время сервера по часам устройства: сроки считаются по нему. */
    now: () => number;
    fetchState: () => Promise<void>;
    /** Кладёт оценку в очередь и возвращает предсказанный срок для тоста. */
    record: (id: string, verdict: TVerdict) => IProgress | null;
    /** Снимает последнюю оценку, пока она не уехала. `false` — уже поздно. */
    cancelLast: () => boolean;
    flush: () => Promise<void>;
}
