// #region Imports
// Types
import type { Ref } from 'vue';

import type { ISwipeActions } from '../types/swipe';

// Vue
import { onBeforeUnmount, onMounted } from 'vue';
// #endregion

// Ход короче этого считается нажатием: палец никогда не стоит на месте ровно.
const DISTANCE = 48;

/**
 * Разбирает жесты по элементу: нажатие и горизонтальные свайпы.
 *
 * Нажатие живёт здесь, а не отдельным обработчиком `click`: клик приходит и после
 * свайпа, и карточка успевала бы перевернуться в тот же миг, когда уезжает. Одна
 * точка решения на весь жест снимает вопрос порядка событий.
 */
export function useSwipe(target: Ref<HTMLElement | null>, actions: ISwipeActions): void {
    let startX = 0;
    let startY = 0;
    let tracking = false;

    /**
     * Запоминает начало жеста и забирает указатель себе.
     */
    function handleDown(event: PointerEvent): void {
        // Без захвата палец, ушедший за край сцены, отдал бы pointerup другому
        // элементу — и жест потерялся бы на середине.
        (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);

        startX = event.clientX;
        startY = event.clientY;
        tracking = true;
    }

    /**
     * Решает, чем был жест: нажатием, свайпом или ничем.
     */
    function handleUp(event: PointerEvent): void {
        if (!tracking) return;
        tracking = false;

        const byX = event.clientX - startX;
        const byY = event.clientY - startY;

        if (Math.abs(byX) < DISTANCE) {
            actions.tap();
            return;
        }

        // Горизонталь должна перевешивать: наклонное движение — это прокрутка длинной
        // карточки или жест самого клиента Telegram, и перехватывать его нельзя.
        if (Math.abs(byX) <= Math.abs(byY)) return;

        if (byX < 0) {
            actions.left();
            return;
        }

        actions.right();
    }

    /**
     * Прерванный жест: система забрала указатель себе.
     */
    function handleCancel(): void {
        tracking = false;
    }

    onMounted(() => {
        target.value?.addEventListener('pointerdown', handleDown);
        target.value?.addEventListener('pointerup', handleUp);
        target.value?.addEventListener('pointercancel', handleCancel);
    });

    onBeforeUnmount(() => {
        target.value?.removeEventListener('pointerdown', handleDown);
        target.value?.removeEventListener('pointerup', handleUp);
        target.value?.removeEventListener('pointercancel', handleCancel);
    });
}
