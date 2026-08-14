import type { ComputedRef } from 'vue';

import type { IEntry } from './entry';

/** Карточка в прогоне: что показывать и какой стороной вперёд. */
export interface IRunItem {
    id: string;
    /** Русский вперёд: лицо — перевод, оборот — арабское. */
    isReversed: boolean;
}

/** Прогон, каким он лежит в `localStorage`: список карточек и место в нём. */
export interface ISavedRun {
    items: IRunItem[];
    index: number;
}

/** Карточка прогона с подобранной записью колоды. */
export interface IRunCard {
    entry: IEntry;
    isReversed: boolean;
}

/** Сторона карточки: что написано и каким письмом. */
export interface ICardSide {
    text: string;
    isArabic: boolean;
}

/** Куда уезжает карточка при перелистывании; имена — классы переходов Vue. */
export type TSlide = 'slide-forward' | 'slide-back';

export interface IUseRun {
    card: ComputedRef<IRunCard | null>;
    /** Человеческий номер карточки, от единицы. */
    position: ComputedRef<number>;
    total: ComputedRef<number>;
    hasPrev: ComputedRef<boolean>;
    hasNext: ComputedRef<boolean>;
    restore: () => void;
    /** Прогон по переданным карточкам: всей колоде или одной теме. */
    start: (selected: IEntry[]) => void;
    next: () => void;
    prev: () => void;
    finish: () => void;
}
