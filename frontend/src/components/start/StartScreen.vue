<script setup lang="ts">
    // #region Imports
    // Utils
    import { plural } from '../../utils/plural';

    // Vue
    import { computed } from 'vue';

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
        start: [];
    }>();
    // #endregion

    // #region Data
    const WORD_FORMS: [string, string, string] = ['слово', 'слова', 'слов'];
    // #endregion

    // #region Computed
    const deckSize = computed<string>(
        () => `В колоде ${props.total} ${plural(props.total, WORD_FORMS)}`,
    );
    // #endregion

    // #region Methods
    /**
     * Просит начать прогон по всей колоде.
     */
    function handleStart(): void {
        emit('start');
    }
    // #endregion
</script>

<template>
    <section :class="$style.StartScreen">
        <h1 :class="$style.StartScreen__title" dir="rtl" lang="ar">مفردات</h1>

        <p v-if="props.total === 0" :class="$style.StartScreen__empty">
            Колода пуста. Добавь слова через бота или админку.
        </p>

        <div v-else :class="$style.StartScreen__action">
            <p :class="$style.StartScreen__size">{{ deckSize }}</p>
            <UiButton @click="handleStart">Начать тренировку</UiButton>
        </div>
    </section>
</template>

<style module lang="scss">
    .StartScreen {
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

        &__action {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }

        &__size {
            color: var(--base-500);
            font-size: 1.4rem;
            text-align: center;
        }
    }
</style>
