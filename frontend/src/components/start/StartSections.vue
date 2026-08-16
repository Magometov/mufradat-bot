<script setup lang="ts">
    // #region Imports
    // Types
    import type { Component } from 'vue';

    import type { ITheme } from '../../types/theme';

    // Vue
    import { computed } from 'vue';

    // Components
    import UiButton from '../ui/UiButton.vue';

    // Icons
    import {
        ArrowLeftRight,
        Activity,
        Box,
        Hash,
        HelpCircle,
        Layers,
        MessageCircle,
        Sparkles,
        Users,
    } from '@lucide/vue';
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

    // #region Constants
    // Значок должен подсказывать содержимое, а не украшать кнопку: рукопожатие у
    // «Знакомства» и молния у «Глаголов» не подсказывали ничего.
    const SECTION_ICONS: Record<string, Component> = {
        last_lesson: Sparkles,
        numbers: Hash,
        family: Users,
        greetings: MessageCircle,
        verbs: Activity,
        antonyms: ArrowLeftRight,
        nouns: Box,
        questions: HelpCircle,
    };

    const DEFAULT_ICON: Component = Layers;

    // Накопитель свежих карточек висит первым и крупнее прочих: его открывают чаще всего.
    const PINNED = 'last_lesson';
    // #endregion

    // #region Computed
    const pinnedSection = computed<ITheme | undefined>(() =>
        props.sections.find((section) => section.slug === PINNED),
    );

    const otherSections = computed<ITheme[]>(() =>
        props.sections.filter((section) => section.slug !== PINNED),
    );
    // #endregion

    // #region Methods
    /**
     * Просит прогон по всем разделам режима.
     */
    function handleSelectAll(): void {
        emit('select', null);
    }

    /**
     * Просит прогон по одному разделу.
     */
    function handleSelect(slug: string): void {
        emit('select', slug);
    }

    /**
     * Возвращает на выбор режима.
     */
    function handleBack(): void {
        emit('back');
    }

    /**
     * Значок раздела; у незнакомого кода — общий.
     */
    function getIconForSection(slug: string): Component {
        return SECTION_ICONS[slug] ?? DEFAULT_ICON;
    }
    // #endregion
</script>

<template>
    <section :class="$style.StartSections">
        <header :class="$style.StartSections__head">
            <UiButton variant="ghost" @click="handleBack">←</UiButton>

            <h2 :class="$style.StartSections__title">{{ props.title }}</h2>
        </header>

        <div :class="$style.StartSections__choice">
            <UiButton
                v-if="pinnedSection"
                :class="$style.StartSections__button"
                variant="accent"
                size="large"
                @click="handleSelect(pinnedSection.slug)"
            >
                <component :is="getIconForSection(pinnedSection.slug)" :size="20" />
                {{ pinnedSection.name }}
            </UiButton>

            <UiButton
                :class="$style.StartSections__button"
                variant="plain"
                @click="handleSelectAll"
            >
                Все разделы
            </UiButton>

            <div v-if="otherSections.length > 0" :class="$style.StartSections__list">
                <UiButton
                    v-for="section in otherSections"
                    :key="section.slug"
                    :class="$style.StartSections__button"
                    variant="plain"
                    @click="handleSelect(section.slug)"
                >
                    <component
                        :is="getIconForSection(section.slug)"
                        :size="20"
                        :class="$style.StartSections__icon"
                    />
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
            gap: 0.4rem;
        }

        &__title {
            font-size: 1.9rem;
            font-weight: 600;
        }

        &__choice {
            display: flex;
            flex: 1;
            flex-direction: column;
            justify-content: center;
            gap: 1.2rem;
        }

        // Раскладка кнопки задаётся здесь, а не через её класс из UiButton: там свой
        // CSS-модуль, и его имена в этом файле не совпадут с настоящими.
        &__button {
            width: 100%;
            // Подпись переносится, а не режется: «Существительные» в половину ширины
            // одной строкой не помещается, а сокращать название незачем.
            text-wrap: balance;
        }

        &__icon {
            color: var(--muted);
        }

        &__list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.2rem;

            // Нечётная последняя кнопка занимает ряд целиком, иначе рядом дыра.
            > *:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }
        }
    }
</style>
