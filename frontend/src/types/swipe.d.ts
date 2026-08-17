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
    /** Куда тянут: -1 влево, 1 вправо, 0 — палец отпущен или сдвиг мал. */
    direction: Ref<number>;
}
