<script setup lang="ts">
    // #region Imports
    // Types
    import type { ITheme } from '../../types/theme';

    // Vue
    import { computed } from 'vue';

    // Components
    import UiButton from '../ui/UiButton.vue';

    // Icons
    import { 
        BookOpen, 
        Hash, 
        Users, 
        Handshake, 
        Zap, 
        ArrowLeftRight, 
        FileText, 
        HelpCircle,
        Layers
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
    const SECTION_ICONS: Record<string, any> = {
        last_lesson: BookOpen,
        numbers: Hash,
        family: Users,
        greetings: Handshake,
        verbs: Zap,
        antonyms: ArrowLeftRight,
        nouns: FileText,
        questions: HelpCircle,
    };

    const DEFAULT_ICON = Layers;
    // #endregion

    // #region Computed
    const lastLessonSection = computed<ITheme | undefined>(() => {
        return props.sections.find((section) => section.slug === 'last_lesson');
    });

    const otherSections = computed<ITheme[]>(() => {
        return props.sections.filter((section) => section.slug !== 'last_lesson');
    });
    // #endregion

    // #region Methods
    function handleSelectAll(): void {
        emit('select', null);
    }

    function handleSelect(slug: string): void {
        emit('select', slug);
    }

    function handleBack(): void {
        emit('back');
    }

    function getIconForSection(slug: string): any {
        return SECTION_ICONS[slug] || DEFAULT_ICON;
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
            <div v-if="lastLessonSection" :class="$style.StartSections__lastLesson">
                <UiButton variant="accent" size="large" @click="handleSelect(lastLessonSection.slug)">
                    <component :is="getIconForSection(lastLessonSection.slug)" :size="20" :class="$style.StartSections__icon" />
                    {{ lastLessonSection.name }}
                </UiButton>
            </div>

            <UiButton variant="soft" size="large" @click="handleSelectAll">Все разделы</UiButton>

            <div v-if="otherSections.length > 0" :class="$style.StartSections__list">
                <UiButton
                    v-for="section in otherSections"
                    :key="section.slug"
                    variant="soft"
                    @click="handleSelect(section.slug)"
                >
                    <component :is="getIconForSection(section.slug)" :size="18" :class="$style.StartSections__iconSmall" />
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

        &__lastLesson {
            margin-bottom: 0.5rem;

            > * {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.8rem;
                width: 100%;
                font-weight: 600;
            }
        }

        &__icon {
            flex-shrink: 0;
        }

        &__iconSmall {
            flex-shrink: 0;
            opacity: 0.8;
        }

        &__choice > .UiButton--soft {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            font-weight: 500;
        }

        &__list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;

            .UiButton--soft {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.6rem;
            }

            > *:last-child:nth-child(odd) {
                grid-column: 1 / -1;
            }
        }
    }
</style>
