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
        BookOpen,
        Handshake,
        Hash,
        HelpCircle,
        FileText,
        Layers,
        Users,
        Zap,
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
    const SECTION_ICONS: Record<string, Component> = {
        last_lesson: BookOpen,
        numbers: Hash,
        family: Users,
        greetings: Handshake,
        verbs: Zap,
        antonyms: ArrowLeftRight,
        nouns: FileText,
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
     * Иконка раздела; у незнакомого кода — общая.
     */
    function getIconForSection(slug: string): Component {
        return SECTION_ICONS[slug] ?? DEFAULT_ICON;
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
            <UiButton
                v-if="pinnedSection"
                :class="$style.StartSections__button"
                variant="accent"
                size="large"
                @click="handleSelect(pinnedSection.slug)"
            >
                <component
                    :is="getIconForSection(pinnedSection.slug)"
                    :size="20"
                    :class="$style.StartSections__icon"
                />
                {{ pinnedSection.name }}
            </UiButton>

            <UiButton
                :class="$style.StartSections__button"
                variant="soft"
                size="large"
                @click="handleSelectAll"
            >
                Все разделы
            </UiButton>

            <div v-if="otherSections.length > 0" :class="$style.StartSections__list">
                <UiButton
                    v-for="section in otherSections"
                    :key="section.slug"
                    :class="$style.StartSections__button"
                    variant="soft"
                    @click="handleSelect(section.slug)"
                >
                    <component
                        :is="getIconForSection(section.slug)"
                        :size="18"
                        :class="$style.StartSections__iconSmall"
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
            gap: 0.8rem;
        }

        &__title {
            margin: 0;
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

        // Раскладка кнопки задаётся здесь, а не через её класс из UiButton: там свой
        // CSS-модуль, и его имена в этом файле не совпадут с настоящими.
        &__button {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.8rem;
            width: 100%;
        }

        &__icon {
            flex-shrink: 0;
        }

        &__iconSmall {
            flex-shrink: 0;
            opacity: 0.8;
        }

        &__list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;

            // Нечётная последняя кнопка занимает ряд целиком, иначе рядом дыра.
            > *:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }
        }
    }
</style>
