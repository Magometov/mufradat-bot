<script setup lang="ts">
    // #region Imports
    // Types
    import type { TRunMode } from '../../types/selection';

    // Utils
    import { MODE_TITLES } from '../../utils/modes';

    // Components
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            total: number;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        select: [mode: TRunMode];
    }>();
    // #endregion

    // #region Methods
    /**
     * Просит перейти к разделам с выбранным режимом.
     */
    function handleSelect(mode: TRunMode): void {
        emit('select', mode);
    }
    // #endregion
</script>

<template>
    <section :class="$style.StartMode">
        <h1 :class="$style.StartMode__title" dir="rtl" lang="ar">مفردات</h1>

        <p v-if="props.total === 0" :class="$style.StartMode__empty">
            Колода пуста. Добавь слова через бота или админку.
        </p>

        <div v-else :class="$style.StartMode__choice">
            <UiButton @click="handleSelect('words')">{{ MODE_TITLES.words }}</UiButton>

            <UiButton variant="soft" @click="handleSelect('all')">{{ MODE_TITLES.all }}</UiButton>
        </div>
    </section>
</template>

<style module lang="scss">
    .StartMode {
        display: flex;
        flex: 1;
        flex-direction: column;
        justify-content: center;
        gap: 4rem;

        &__title {
            font-family: var(--font-arabic);
            font-size: 4.8rem;
            font-weight: 400;
            line-height: 1.6;
            text-align: center;
        }

        &__empty {
            color: var(--base-500);
            text-align: center;
        }

        &__choice {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }
    }
</style>
