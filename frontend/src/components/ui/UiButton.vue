<script setup lang="ts">
    import type { IUiButtonProps } from '../../types/ui';

    const props = withDefaults(defineProps<IUiButtonProps & { size?: 'default' | 'large' }>(), {
        variant: 'primary',
        isDisabled: false,
        size: 'default',
    });
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
        transition: opacity 0.15s ease, transform 0.15s ease, box-shadow 0.2s ease;

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

        &--accent {
            background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-400) 100%);
            color: var(--on-primary);
            box-shadow: 0 4px 16px rgba(var(--primary-500-rgb), 0.35);
            animation: pulse-glow 2.5s ease-in-out infinite;

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
            font-size: 1.7rem;
            font-weight: 600;
        }
    }

    @keyframes pulse-glow {
        0%, 100% {
            box-shadow: 0 4px 16px rgba(var(--primary-500-rgb), 0.35);
        }
        50% {
            box-shadow: 0 4px 24px rgba(var(--primary-500-rgb), 0.55);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .UiButton--accent {
            animation: none;
        }
    }
</style>
