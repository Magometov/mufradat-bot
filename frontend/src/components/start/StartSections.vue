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
            title: string;
            sections: ITheme[];
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        select: [theme: string | null];
        back: [];
    }>();
    // #endregion

    // #region Methods
    /**
     * Прогон по всему выбранному режиму, без деления на разделы.
     */
    function handleSelectAll(): void {
        emit('select', null);
    }

    /**
     * Прогон по одному разделу.
     */
    function handleSelect(slug: string): void {
        emit('select', slug);
    }

    /**
     * Возвращает к выбору режима.
     */
    function handleBack(): void {
        emit('back');
    }
    // #endregion
</script>

<template>
    <section :class="$style.StartSections">
        <header :class="$style.StartSections__head">
            <UiButton variant="ghost" @click="handleBack">← Назад</UiButton>

            <h2 :class="$style.StartSections__title">{{ props.title }}</h2>
        </header>

        <div :class="$style.StartSections__choice">
            <UiButton @click="handleSelectAll">Все разделы</UiButton>

            <div v-if="props.sections.length > 0" :class="$style.StartSections__list">
                <UiButton
                    v-for="section in props.sections"
                    :key="section.slug"
                    variant="soft"
                    @click="handleSelect(section.slug)"
                >
                    {{ section.name }}
                </UiButton>
            </div>
        </div>
    </section>
</template>

<style module lang="scss">
    .StartSections {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 2rem;

        &__head {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        &__title {
            font-size: 1.6rem;
            font-weight: 500;
        }

        &__choice {
            display: flex;
            flex: 1;
            flex-direction: column;
            justify-content: center;
            gap: 2rem;
        }

        // Две колонки: длинные названия переносятся, кнопки тянутся по высоте строки.
        &__list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;

            // Разделов может остаться нечётное число, и последний висел бы половинкой
            // в левой колонке. Условие на `nth-child(odd)` держит вид и при чётном списке.
            > *:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }
        }
    }
</style>
