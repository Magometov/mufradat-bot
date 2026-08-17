<script setup lang="ts">
    // #region Imports
    // Types
    import type { TRunKind } from '../../types/run';

    // Vue
    import { computed } from 'vue';

    // Components
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            /** Повторение оценивает, просмотр листает. */
            kind: TRunKind;
            position?: number;
            total?: number;
            hasPrev?: boolean;
            hasNext?: boolean;
        }>(),
        { position: 0, total: 0, hasPrev: false, hasNext: false },
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        know: [];
        forgot: [];
        prev: [];
        next: [];
        finish: [];
    }>();
    // #endregion

    // #region Computed
    // На последней карточке кнопка закрывает прогон, поэтому и подпись у неё другая.
    const nextLabel = computed<string>(() => (props.hasNext ? 'Далее' : 'Готово'));
    // #endregion

    // #region Methods
    /**
     * Шаг назад по прогону.
     */
    function handlePrev(): void {
        emit('prev');
    }

    /**
     * Шаг вперёд, а на последней карточке — конец прогона: список кончился, и
     * закрывать его больше нечем.
     */
    function handleNext(): void {
        if (props.hasNext) {
            emit('next');
            return;
        }

        emit('finish');
    }
    // #endregion
</script>

<template>
    <footer :class="$style.RunControls">
        <template v-if="props.kind === 'review'">
            <UiButton variant="plain" @click="emit('forgot')">Не помню</UiButton>

            <UiButton variant="accent" @click="emit('know')">Помню</UiButton>
        </template>

        <template v-else>
            <UiButton variant="plain" :is-disabled="!props.hasPrev" @click="handlePrev">
                Назад
            </UiButton>

            <!-- Счётчик объявляется вслух: для того, кто листает с клавиатуры, это
                 единственный признак, что карточка сменилась. -->
            <p :class="$style.RunControls__counter" aria-live="polite">
                {{ props.position }} / {{ props.total }}
            </p>

            <UiButton variant="accent" @click="handleNext">{{ nextLabel }}</UiButton>
        </template>
    </footer>
</template>

<style module lang="scss">
    .RunControls {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;

        &__counter {
            color: var(--muted);
            font-size: 1.5rem;
            font-variant-numeric: tabular-nums;
        }
    }
</style>
