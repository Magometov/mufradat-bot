<script setup lang="ts">
    // #region Imports
    // Types
    import type { ITheme } from '../../types/theme';

    // Components
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            total: number;
            themes: ITheme[];
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        start: [theme: string | null];
    }>();
    // #endregion

    // #region Methods
    /**
     * Просит начать прогон по всей колоде.
     */
    function handleStartAll(): void {
        emit('start', null);
    }

    /**
     * Просит начать прогон по одной теме.
     */
    function handleStartTheme(slug: string): void {
        emit('start', slug);
    }
    // #endregion
</script>

<template>
    <section :class="$style.StartScreen">
        <h1 :class="$style.StartScreen__title" dir="rtl" lang="ar">مفردات</h1>

        <p v-if="props.total === 0" :class="$style.StartScreen__empty">
            Колода пуста. Добавь слова через бота или админку.
        </p>

        <div v-else :class="$style.StartScreen__choice">
            <UiButton @click="handleStartAll">Все слова</UiButton>

            <div v-if="props.themes.length > 0" :class="$style.StartScreen__themes">
                <UiButton
                    v-for="theme in props.themes"
                    :key="theme.slug"
                    variant="soft"
                    @click="handleStartTheme(theme.slug)"
                >
                    {{ theme.name }}
                </UiButton>
            </div>
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

        &__choice {
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        // Две колонки: длинные названия переносятся, кнопки тянутся по высоте строки.
        &__themes {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;

            // Тем нечётное число, и последняя иначе висела бы половинкой в левой
            // колонке. Условие на `nth-child(odd)` держит вид и при чётном списке.
            > *:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }
        }
    }
</style>
