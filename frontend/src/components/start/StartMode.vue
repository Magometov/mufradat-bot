<script setup lang="ts">
    // #region Imports
    // Types
    import type { TRunMode } from '../../types/selection';

    // Utils
    import { MODE_TITLES } from '../../utils/modes';

    // Components
    import StartAppearance from './StartAppearance.vue';
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
        <!-- Оформление меняют здесь и больше нигде: это настройка, а не действие
             прогона, в разделах и карточках ей делать нечего. -->
        <StartAppearance />

        <div :class="$style.StartMode__body">
            <!-- Стопка вместо заголовка: название лежит на верхней карточке, и с первого
             экрана видно, чем тут занимаются. -->
            <div :class="$style.StartMode__stack" aria-hidden="true">
                <div :class="[$style.StartMode__card, $style['StartMode__card--back']]"></div>
                <div :class="[$style.StartMode__card, $style['StartMode__card--mid']]"></div>
                <div :class="[$style.StartMode__card, $style['StartMode__card--front']]">
                    <span :class="$style.StartMode__title" dir="rtl" lang="ar">مفردات</span>
                </div>
            </div>

            <h1 :class="$style.StartMode__name" dir="rtl" lang="ar">مفردات</h1>

            <p v-if="props.total === 0" :class="$style.StartMode__empty">
                Колода пуста. Добавь слова через бота или админку.
            </p>

            <div v-else :class="$style.StartMode__choice">
                <UiButton variant="accent" @click="handleSelect('words')">
                    {{ MODE_TITLES.words }}
                </UiButton>

                <UiButton variant="plain" @click="handleSelect('all')">
                    {{ MODE_TITLES.all }}
                </UiButton>
            </div>
        </div>
    </section>
</template>

<style module lang="scss">
    .StartMode {
        display: flex;
        flex: 1;
        flex-direction: column;

        // Кнопка оформления стоит сверху, а стопка с выбором — по центру остатка.
        &__body {
            display: flex;
            flex: 1;
            flex-direction: column;
            justify-content: center;
            gap: 4.4rem;
        }

        &__stack {
            position: relative;
            height: 25rem;
        }

        &__card {
            position: absolute;
            left: 50%;
            border-radius: 2.2rem;
            background: var(--behind);
        }

        // Нижние повёрнуты и выглядывают из-под верхней: без них это просто плашка.
        &__card--back {
            top: 0;
            width: 20rem;
            height: 23.6rem;
            margin-left: -10rem;
            box-shadow: 0 0.8rem 2rem -1rem var(--under);
            transform: rotate(-7deg);
        }

        &__card--mid {
            top: 0.6rem;
            width: 21rem;
            height: 23.4rem;
            margin-left: -10.6rem;
            box-shadow: 0 0.8rem 2rem -1rem var(--under);
            transform: rotate(4deg);
        }

        &__card--front {
            top: 1.2rem;
            display: flex;
            width: 22rem;
            height: 23rem;
            align-items: center;
            justify-content: center;
            margin-left: -11rem;
            background: var(--surface);
            box-shadow: var(--lift);
        }

        &__title {
            font-family: var(--font-arabic);
            font-size: 4.4rem;
            line-height: 1.7;
        }

        // Название нарисовано на карточке, поэтому заголовок нужен только тем, кто
        // страницу не видит: скринридеру и поиску.
        &__name {
            position: absolute;
            width: 1px;
            height: 1px;
            overflow: hidden;
            clip-path: inset(50%);
            white-space: nowrap;
        }

        &__empty {
            color: var(--muted);
            text-align: center;
        }

        &__choice {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }
    }
</style>
