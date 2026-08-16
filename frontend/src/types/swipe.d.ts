/** Что делать по жестам. Нажатие здесь же: его отличают от свайпа по одному ходу. */
export interface ISwipeActions {
    tap: () => void;
    left: () => void;
    right: () => void;
}
