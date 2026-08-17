import type { Ref } from 'vue';

/** Чем оказался жест. */
export type TGesture = 'tap' | 'left' | 'right';

/** Что делать по жестам. Нажатие здесь же: его отличают от свайпа по одному ходу. */
export interface ISwipeActions {
    tap: () => void;
    left: () => void;
    right: () => void;
}

export interface IUseSwipe {
    /** На сколько карточка утянута от пальца. Ноль — палец отпущен. */
    shift: Ref<number>;
}
