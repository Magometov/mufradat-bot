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
            /** Видна ли новая логика: без неё экран остаётся сегодняшним. */
            isReview?: boolean;
            /** Сколько карточек назначено на сегодня по всей колоде. */
            due?: number;
            /** Когда придёт ближайшая, если на сегодня ничего нет. */
            next?: string;
            /** Есть ли куда возвращаться: в просмотре колоды — на главную. */
            canBack?: boolean;
        }>(),
        { isReview: false, due: 0, next: '', canBack: false },
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        select: [mode: TRunMode];
        repeat: [];
        view: [];
        back: [];
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
        <header :class="$style.StartMode__head">
            <UiButton v-if="props.canBack" variant="ghost" @click="emit('back')">←</UiButton>

            <!-- Оформление меняют здесь и больше нигде: это настройка, а не действие
                 прогона, в разделах и карточках ей делать нечего. -->
            <StartAppearance :class="$style.StartMode__appearance" />
        </header>

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
                <template v-if="props.isReview">
                    <UiButton v-if="props.due > 0" variant="accent" @click="emit('repeat')">
                        Повторить
                    </UiButton>

                    <p v-else :class="$style.StartMode__empty">
                        На сегодня всё повторено.<br />
                        Ближайшее слово — <b>{{ props.next }}</b
                        >.
                    </p>

                    <!-- Разделитель словами: без него кнопки режима читаются как
                         соперники «Повторить», хотя ведут к выбору раздела. -->
                    <p :class="$style.StartMode__label">или выбрать раздел</p>
                </template>

                <UiButton
                    :variant="props.isReview ? 'plain' : 'accent'"
                    @click="handleSelect('words')"
                >
                    {{ MODE_TITLES.words }}
                </UiButton>

                <UiButton variant="plain" @click="handleSelect('all')">
                    {{ MODE_TITLES.all }}
                </UiButton>

                <button
                    v-if="props.isReview"
                    :class="$style.StartMode__view"
                    type="button"
                    @click="emit('view')"
                >
                    Посмотреть колоду
                    <small>листать без оценок</small>
                </button>
            </div>
        </div>
    </section>
</template>

<style module lang="scss">
    .StartMode {
        display: flex;
        flex: 1;
        flex-direction: column;

        // Возврат слева, оформление справа — как в шапке разделов.
        &__head {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        &__appearance {
            margin-left: auto;
        }

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

            b {
                color: var(--ink);
                font-weight: 600;
            }
        }

        &__label {
            color: var(--muted);
            font-size: 1.4rem;
            text-align: center;
        }

        // Обводка вместо заливки: кнопка должна читаться кнопкой, но стоять третьей по
        // весу — у остальных есть фон и тень, у неё только контур.
        &__view {
            padding: 1.2rem 2rem;
            border: 1px solid var(--track);
            border-radius: 1.6rem;
            background: none;
            color: var(--muted);
            font-family: inherit;
            font-size: 1.5rem;
            font-weight: 500;
            cursor: pointer;

            small {
                display: block;
                margin-top: 0.2rem;
                color: var(--muted);
                font-size: 1.2rem;
                font-weight: 400;
                opacity: 0.8;
            }

            &:focus-visible {
                outline: 2px solid var(--accent);
                outline-offset: 2px;
            }
        }

        &__choice {
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
        }
    }
</style>
