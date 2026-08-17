// #region Imports
// Types
import type { Ref } from 'vue';

import type { ISwipeActions, IUseSwipe } from '../types/swipe';

// Utils
import { decide } from '../utils/gesture';

// Vue
import { onBeforeUnmount, onMounted, ref } from 'vue';
// #endregion

/**
 * Разбирает жесты по элементу: нажатие и горизонтальные свайпы.
 *
 * Карточка едет за пальцем, поэтому `shift` меняется на каждом движении: без этого
 * свайп кажется тяжёлым — палец идёт, а на экране до конца жеста ничего не происходит.
 *
 * Нажатие живёт здесь, а не отдельным обработчиком `click`: клик приходит и после
 * свайпа, и карточка успевала бы перевернуться в тот же миг, когда уезжает.
 */
export function useSwipe(target: Ref<HTMLElement | null>, actions: ISwipeActions): IUseSwipe {
    const shift = ref(0);

    let startX = 0;
    let startY = 0;
    let startedAt = 0;
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
        startedAt = event.timeStamp;
        tracking = true;
    }

    /**
     * Тянет карточку за пальцем, пока жест горизонтальный.
     */
    function handleMove(event: PointerEvent): void {
        if (!tracking) return;

        const byX = event.clientX - startX;

        shift.value = Math.abs(byX) > Math.abs(event.clientY - startY) ? byX : 0;
    }

    /**
     * Решает, чем был жест, и отпускает карточку.
     */
    function handleUp(event: PointerEvent): void {
        if (!tracking) return;

        tracking = false;
        shift.value = 0;

        const width = target.value?.clientWidth ?? 0;
        const gesture = decide(
            event.clientX - startX,
            event.clientY - startY,
            event.timeStamp - startedAt,
            width,
        );

        if (gesture === null) return;

        actions[gesture]();
    }

    /**
     * Прерванный жест: система забрала указатель себе.
     */
    function handleCancel(): void {
        tracking = false;
        shift.value = 0;
    }

    onMounted(() => {
        target.value?.addEventListener('pointerdown', handleDown);
        target.value?.addEventListener('pointermove', handleMove);
        target.value?.addEventListener('pointerup', handleUp);
        target.value?.addEventListener('pointercancel', handleCancel);
    });

    onBeforeUnmount(() => {
        target.value?.removeEventListener('pointerdown', handleDown);
        target.value?.removeEventListener('pointermove', handleMove);
        target.value?.removeEventListener('pointerup', handleUp);
        target.value?.removeEventListener('pointercancel', handleCancel);
    });

    return { shift };
}
