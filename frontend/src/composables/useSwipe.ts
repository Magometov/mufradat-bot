// #region Imports
// Types
import type { Ref } from 'vue';

import type { ISwipeActions, IUseSwipe } from '../types/swipe';

// Utils
import { MARK_AT, decide } from '../utils/gesture';

// Vue
import { onBeforeUnmount, onMounted, ref } from 'vue';
// #endregion

/**
 * Разбирает жесты по элементу: нажатие и горизонтальные свайпы.
 *
 * Утягиваемый слой ищется по признаку `data-mover` и двигается записью в стиль, а не
 * через реактивность: иначе каждое движение пальца перерисовывало бы компонент, и жест
 * подтормаживал бы на длинных карточках.
 *
 * Нажатие живёт здесь, а не отдельным обработчиком `click`: клик приходит и после
 * свайпа, и карточка успевала бы перевернуться в тот же миг, когда уезжает.
 */
export function useSwipe(target: Ref<HTMLElement | null>, actions: ISwipeActions): IUseSwipe {
    // Сторона, в которую тянут, и только она: метка меняется редко, а сдвиг — на каждом
    // кадре, и держать его в реактивной ссылке незачем.
    const direction = ref(0);

    let startX = 0;
    let startY = 0;
    let startedAt = 0;
    let tracking = false;
    let shift = 0;
    let frame = 0;
    let mover: HTMLElement | null = null;

    /**
     * Утягиваемый слой текущей карточки.
     */
    function findMover(): HTMLElement | null {
        return target.value?.querySelector<HTMLElement>('[data-mover]') ?? null;
    }

    /**
     * Рисует сдвиг: один раз на кадр, чтобы не гнать стиль чаще, чем экран обновляется.
     */
    function draw(): void {
        frame = 0;

        if (mover === null) return;

        // `translate3d` — чтобы слой ушёл на GPU и кадры не считались заново.
        mover.style.transform = `translate3d(${shift}px, 0, 0) rotate(${shift / 26}deg)`;
    }

    /**
     * Возвращает слой на место и отдаёт переход обратно стилям.
     */
    function release(): void {
        if (mover === null) return;

        mover.style.transition = '';
        mover.style.transform = '';
        mover = null;
    }

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
        shift = 0;
        mover = findMover();

        // Пока палец ведёт, перехода нет: иначе слой тянется с задержкой.
        if (mover !== null) mover.style.transition = 'none';
    }

    /**
     * Тянет карточку за пальцем, пока жест горизонтальный.
     */
    function handleMove(event: PointerEvent): void {
        if (!tracking) return;

        const byX = event.clientX - startX;

        shift = Math.abs(byX) > Math.abs(event.clientY - startY) ? byX : 0;

        const side = Math.abs(shift) < MARK_AT ? 0 : Math.sign(shift);
        if (side !== direction.value) direction.value = side;

        if (frame === 0) frame = requestAnimationFrame(draw);
    }

    /**
     * Решает, чем был жест, и отпускает карточку.
     */
    function handleUp(event: PointerEvent): void {
        if (!tracking) return;

        tracking = false;
        direction.value = 0;
        cancelAnimationFrame(frame);
        frame = 0;

        const gesture = decide(
            event.clientX - startX,
            event.clientY - startY,
            event.timeStamp - startedAt,
            target.value?.clientWidth ?? 0,
        );

        release();

        if (gesture === null) return;

        actions[gesture]();
    }

    /**
     * Прерванный жест: система забрала указатель себе.
     */
    function handleCancel(): void {
        tracking = false;
        direction.value = 0;
        cancelAnimationFrame(frame);
        frame = 0;
        release();
    }

    onMounted(() => {
        target.value?.addEventListener('pointerdown', handleDown);
        target.value?.addEventListener('pointermove', handleMove);
        target.value?.addEventListener('pointerup', handleUp);
        target.value?.addEventListener('pointercancel', handleCancel);
    });

    onBeforeUnmount(() => {
        cancelAnimationFrame(frame);
        target.value?.removeEventListener('pointerdown', handleDown);
        target.value?.removeEventListener('pointermove', handleMove);
        target.value?.removeEventListener('pointerup', handleUp);
        target.value?.removeEventListener('pointercancel', handleCancel);
    });

    return { direction };
}
