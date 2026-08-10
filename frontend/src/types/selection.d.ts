import type { ComputedRef, Ref } from 'vue';

import type { IEntry } from './entry';
import type { ITheme } from './theme';

/** Что повторяем: только отдельные слова или всё подряд. */
export type TRunMode = 'words' | 'all';

export interface IUseSelection {
    /** `null` — режим ещё не выбран, приложение стоит на первом экране. */
    mode: Ref<TRunMode | null>;
    /** Разделы, в которых для выбранного режима есть карточки. */
    sections: ComputedRef<ITheme[]>;
    choose: (mode: TRunMode) => void;
    /** Карточки для прогона: весь режим или один его раздел. */
    cardsFor: (theme: string | null) => IEntry[];
    reset: () => void;
}
