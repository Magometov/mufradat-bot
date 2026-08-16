<script setup lang="ts">
    // #region Imports
    // Types
    import type { IUiButtonProps } from '../../types/ui';
    // #endregion

    // #region Props
    const props = withDefaults(defineProps<IUiButtonProps>(), {
        variant: 'accent',
        isDisabled: false,
        size: 'default',
    });
    // #endregion
</script>

<template>
    <button
        :class="[
            $style.UiButton,
            $style[`UiButton--${props.variant}`],
            $style[`UiButton--${props.size}`],
        ]"
        :disabled="props.isDisabled"
        type="button"
    >
        <slot />
    </button>
</template>

<style module lang="scss">
    // Границ у кнопок нет: слои в этом виде разделяет тень, а не линия.
    .UiButton {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        padding: 1.6rem 2rem;
        border: 0;
        border-radius: 1.6rem;
        font-size: 1.7rem;
        font-weight: 600;
        cursor: pointer;
        transition:
            opacity 0.15s ease,
            transform 0.15s ease;

        &:disabled {
            opacity: 0.4;
            cursor: default;
        }

        &:active:not(:disabled) {
            transform: scale(0.97);
            opacity: 0.9;
        }

        &:focus-visible {
            outline: 2px solid var(--accent);
            outline-offset: 2px;
        }

        &--accent {
            background: var(--accent);
            color: var(--on-accent);
            box-shadow: var(--lift);
        }

        &--plain {
            background: var(--surface);
            color: var(--ink);
            box-shadow: var(--lift-sm);
            font-weight: 500;
        }

        // Прозрачная кнопка — обычно один значок, и по нему всё равно попадают пальцем:
        // ниже 4.4rem промахиваются.
        &--ghost {
            min-width: 4.4rem;
            min-height: 4.4rem;
            padding: 0.8rem 1rem;
            background: none;
            color: var(--muted);
            font-size: 1.4rem;
            font-weight: 400;
        }

        &--large {
            padding: 1.8rem 2.4rem;
            font-size: 1.8rem;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .UiButton {
            transition: none;

            &:active:not(:disabled) {
                transform: none;
            }
        }
    }
</style>
