<script setup lang="ts">
    // #region Imports
    // Types
    import type { IUiButtonProps } from '../../types/ui';
    // #endregion

    // #region Props
    const props = withDefaults(defineProps<IUiButtonProps>(), {
        variant: 'primary',
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
    .UiButton {
        padding: 1.4rem 2rem;
        border: 1px solid transparent;
        border-radius: 1.4rem;
        font-size: 1.6rem;
        font-weight: 500;
        cursor: pointer;
        transition:
            opacity 0.15s ease,
            transform 0.15s ease,
            box-shadow 0.2s ease;

        &:disabled {
            opacity: 0.4;
            cursor: default;
        }

        &:active:not(:disabled) {
            transform: scale(0.97);
            opacity: 0.9;
        }

        &--primary {
            background: var(--primary-500);
            color: var(--on-primary);
        }

        // Свечение постоянное, а не пульсирующее: этот вариант стоит и на «Далее»,
        // то есть мигал бы весь прогон, ничего при этом не сообщая.
        &--accent {
            background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-400) 100%);
            color: var(--on-primary);
            box-shadow: 0 4px 16px rgba(var(--primary-500-rgb), 0.35);

            &:active:not(:disabled) {
                box-shadow: 0 2px 8px rgba(var(--primary-500-rgb), 0.3);
            }
        }

        &--soft {
            border-color: var(--base-200);
            background: var(--base-50);
            color: var(--base-900);
        }

        &--ghost {
            padding: 0.8rem 1rem;
            background: none;
            color: var(--base-500);
            font-size: 1.4rem;
            font-weight: 400;
        }

        &--large {
            padding: 1.6rem 2.4rem;
            font-size: 1.8rem;
            font-weight: 600;
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
