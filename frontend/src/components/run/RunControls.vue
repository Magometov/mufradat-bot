<script setup lang="ts">
    // #region Imports
    // Vue
    import { computed } from 'vue';

    // Components
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            position: number;
            total: number;
            hasPrev: boolean;
            hasNext: boolean;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
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
        <UiButton variant="soft" :is-disabled="!props.hasPrev" @click="handlePrev">
            Назад
        </UiButton>

        <p :class="$style.RunControls__counter">{{ props.position }} / {{ props.total }}</p>

        <UiButton variant="accent" @click="handleNext">{{ nextLabel }}</UiButton>
    </footer>
</template>

<style module lang="scss">
    .RunControls {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;

        &__counter {
            color: var(--base-500);
            font-size: 1.4rem;
            font-variant-numeric: tabular-nums;
        }
    }
</style>
