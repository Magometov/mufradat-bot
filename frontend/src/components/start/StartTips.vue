<script setup lang="ts">
    // #region Imports
    // Types
    import type { IRules } from '../../types/progress';

    // Utils
    import { dayWord } from '../../utils/plural';

    // Vue
    import { computed, ref } from 'vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            /** Лестница сроков показывается настоящей, а не примером из головы. */
            rules: IRules | null;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        close: [];
    }>();
    // #endregion

    // #region Data
    const TOTAL = 5;

    const step = ref(1);
    // #endregion

    // #region Computed
    const isLast = computed<boolean>(() => step.value === TOTAL);

    const ladder = computed<number[]>(() => props.rules?.ladder ?? []);

    const needed = computed<number>(() => props.rules?.needed ?? 2);

    // Ступени пропорциональны срокам: иначе первая читается чертой, а не ступенью.
    const rungs = computed<{ days: number; height: string; delay: string }[]>(() => {
        const longest = Math.max(...ladder.value, 1);

        return ladder.value.map((days, index) => ({
            days,
            height: `${(1.6 + (days / longest) * 6).toFixed(1)}rem`,
            delay: `${index * 0.2}s`,
        }));
    });
    // #endregion

    // #region Methods
    /**
     * Следующий шаг, а с последнего — закрыть.
     */
    function handleNext(): void {
        if (isLast.value) {
            emit('close');
            return;
        }

        step.value += 1;
    }
    // #endregion
</script>

<template>
    <!-- Накладка поверх экрана: первый шаг объясняет кнопки, которые под ней видны. -->
    <div :class="$style.StartTips" role="dialog" aria-modal="true" @click="handleNext">
        <div :class="$style.StartTips__stage">
            <template v-if="step === 1">
                <p :class="$style.StartTips__lead">Три способа заниматься</p>

                <div :class="$style.StartTips__call">
                    <b>Повторить</b>
                    <span>Всё, что назначено на сегодня, по всей колоде.</span>
                </div>

                <div :class="$style.StartTips__call">
                    <b>Только слова · Слова и фразы</b>
                    <span>То же сегодняшнее, но в одном разделе.</span>
                </div>

                <div :class="$style.StartTips__call">
                    <b>Посмотреть колоду</b>
                    <span>Листать просто так, расписание не меняется.</span>
                </div>
            </template>

            <!-- Дальше карточка нарисована здесь же: рассказ идёт до входа в сеанс. -->
            <div v-else-if="step === 2" :class="$style.StartTips__demo">
                <div :class="$style.StartTips__card">
                    <span :class="$style.StartTips__arabic" dir="rtl" lang="ar">كِتَاب</span>
                    <span :class="$style.StartTips__tap" aria-hidden="true"><i></i><b></b></span>
                </div>
            </div>

            <div v-else-if="step === 3" :class="$style.StartTips__demo">
                <div :class="[$style.StartTips__card, $style['StartTips__card--swipe']]">
                    <span :class="$style.StartTips__mark">Помню</span>
                    <span :class="$style.StartTips__ru">книга</span>
                </div>
            </div>

            <div v-else-if="step === 4" :class="$style.StartTips__demo">
                <div :class="$style.StartTips__ladder">
                    <span v-for="rung in rungs" :key="rung.days" :class="$style.StartTips__rung">
                        <i :style="{ height: rung.height, animationDelay: rung.delay }"></i>
                        <small>{{ rung.days }}&nbsp;{{ dayWord(rung.days).slice(0, 1) }}</small>
                    </span>
                </div>
            </div>

            <div v-else :class="$style.StartTips__demo">
                <div :class="$style.StartTips__loop">
                    <i :class="[$style.StartTips__chip, $style['StartTips__chip--hot']]"></i>
                    <i :class="$style.StartTips__chip"></i>
                    <i :class="$style.StartTips__chip"></i>
                    <i :class="$style.StartTips__chip"></i>
                </div>
            </div>
        </div>

        <div :class="$style.StartTips__box" @click.stop>
            <p :class="$style.StartTips__step">Шаг {{ step }} из {{ TOTAL }}</p>

            <template v-if="step === 1">
                <h2 :class="$style.StartTips__head">С чего начать</h2>
                <p :class="$style.StartTips__text">
                    Кнопки над этой подсказкой отвечают на один вопрос — что повторяем.
                </p>
            </template>

            <template v-else-if="step === 2">
                <h2 :class="$style.StartTips__head">Нажми карточку</h2>
                <p :class="$style.StartTips__text">
                    На обороте перевод и картинка. Сначала попробуй вспомнить сам — в этом весь
                    смысл.
                </p>
            </template>

            <template v-else-if="step === 3">
                <h2 :class="$style.StartTips__head">Скажи, как получилось</h2>
                <p :class="$style.StartTips__text">
                    Вспомнил — «Помню», не вспомнил — «Не помню». Быстрее пальцем: смахни вправо или
                    влево.
                </p>
            </template>

            <template v-else-if="step === 4">
                <h2 :class="$style.StartTips__head">Знакомое уходит дальше</h2>
                <p :class="$style.StartTips__text">
                    Каждое «помню» отправляет слово вперёд по этой лестнице. Знакомые слова
                    перестают попадаться — и правильно.
                </p>
            </template>

            <template v-else>
                <h2 :class="$style.StartTips__head">Трудное остаётся рядом</h2>
                <p :class="$style.StartTips__text">
                    Слово, которое не далось, вернётся через пару карточек — и будет возвращаться,
                    пока не вспомнишь его {{ needed }} раза подряд.
                </p>
                <p :class="$style.StartTips__again">
                    Забыл, как это работает? Открой <b>«?»</b> слева наверху — эти шаги всегда там.
                </p>
            </template>

            <div :class="$style.StartTips__nav">
                <button
                    v-if="!isLast"
                    :class="$style.StartTips__skip"
                    type="button"
                    @click="emit('close')"
                >
                    Пропустить
                </button>
                <span v-else></span>

                <span :class="$style.StartTips__dots" aria-hidden="true">
                    <i
                        v-for="index in TOTAL"
                        :key="index"
                        :class="[
                            $style.StartTips__dot,
                            index === step && $style['StartTips__dot--on'],
                        ]"
                    ></i>
                </span>

                <button :class="$style.StartTips__next" type="button" @click="handleNext">
                    {{ isLast ? 'Начать' : 'Далее' }}
                </button>
            </div>
        </div>
    </div>
</template>

<style module lang="scss">
    .StartTips {
        position: fixed;
        z-index: 10;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        // Затемнение слоем, а не размытием: `backdrop-filter` ест кадры на телефоне.
        background: rgba(17, 22, 32, 0.62);
        inset: 0;
        padding: calc(1.6rem + env(safe-area-inset-top)) 1.6rem
            calc(1.6rem + env(safe-area-inset-bottom));
        gap: 1.2rem;

        // Та же колонка, что у приложения: на широком окне подсказка не должна
        // растягиваться на всю страницу, когда кнопки под ней стоят по центру.
        &__stage,
        &__box {
            width: 100%;
            max-width: 52rem;
            margin: 0 auto;
        }

        &__stage {
            display: flex;
            flex: 1;
            flex-direction: column;
            justify-content: center;
            gap: 1rem;
        }

        &__lead {
            color: var(--on-dark, #fff);
            font-size: 1.7rem;
            font-weight: 700;
        }

        &__call {
            padding: 1rem 1.2rem;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 1.4rem;
            background: rgba(255, 255, 255, 0.12);
            color: #fff;

            b {
                display: block;
                font-size: 1.5rem;
            }

            span {
                color: rgba(255, 255, 255, 0.8);
                font-size: 1.4rem;
            }
        }

        &__demo {
            display: flex;
            flex: 1;
            align-items: center;
            justify-content: center;
        }

        &__card {
            position: relative;
            display: flex;
            width: 17rem;
            height: 19rem;
            align-items: center;
            justify-content: center;
            border-radius: 1.8rem;
            background: var(--surface);
            box-shadow: var(--lift);
        }

        &__card--swipe {
            animation: tip-swipe 2.6s ease-in-out infinite;
        }

        &__arabic {
            font-family: var(--font-arabic);
            font-size: 3.4rem;
            line-height: 1.7;
        }

        &__ru {
            font-size: 2.4rem;
            font-weight: 500;
        }

        &__mark {
            position: absolute;
            top: 1.2rem;
            left: 1.2rem;
            padding: 0.4rem 1.2rem;
            border-radius: 1rem;
            background: var(--good-soft);
            color: var(--good);
            font-size: 1.4rem;
            font-weight: 700;
        }

        // Круги нажатия: два, со сдвигом, чтобы жест читался повторяющимся.
        &__tap {
            position: absolute;
            width: 4.8rem;
            height: 4.8rem;

            i,
            b {
                position: absolute;
                border: 2px solid var(--accent);
                border-radius: 50%;
                inset: 0;
                animation: tip-ripple 1.9s ease-out infinite;
            }

            b {
                animation-delay: 0.95s;
            }
        }

        &__ladder {
            display: flex;
            align-items: flex-end;
            gap: 0.8rem;
        }

        &__rung {
            display: flex;
            width: 4rem;
            flex-direction: column;
            justify-content: flex-end;
            gap: 0.6rem;

            // Волна идёт по ступеням одна за другой: так видно, что слово уходит дальше.
            i {
                display: block;
                border-radius: 0.4rem;
                background: rgba(255, 255, 255, 0.32);
                transform-origin: bottom;
                animation: tip-wave 2.4s ease-in-out infinite;
            }

            small {
                color: rgba(255, 255, 255, 0.75);
                font-size: 1.2rem;
                text-align: center;
            }
        }

        &__loop {
            position: relative;
            display: flex;
            width: 100%;
            max-width: 30rem;
            justify-content: space-between;
        }

        &__chip {
            display: block;
            width: 4.4rem;
            height: 6rem;
            border-radius: 0.8rem;
            background: rgba(255, 255, 255, 0.24);
        }

        &__chip--hot {
            background: #fff;
            animation: tip-hop 4.2s ease-in-out infinite;
        }

        &__box {
            padding: 1.6rem;
            border-radius: 1.8rem;
            background: var(--surface);
            box-shadow: var(--lift);
        }

        &__step {
            color: var(--muted);
            font-size: 1.2rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        &__head {
            margin: 0.4rem 0 0.6rem;
            font-size: 1.9rem;
            font-weight: 700;
        }

        &__text {
            color: var(--ink);
            font-size: 1.5rem;
        }

        &__again {
            margin-top: 1.2rem;
            padding-top: 1.2rem;
            border-top: 1px solid var(--track);
            color: var(--muted);
            font-size: 1.4rem;
        }

        &__nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 1.6rem;
        }

        &__skip,
        &__next {
            border: 0;
            font-family: inherit;
            cursor: pointer;
        }

        &__skip {
            padding: 0;
            background: none;
            color: var(--muted);
            font-size: 1.4rem;
        }

        &__next {
            padding: 1rem 1.6rem;
            border-radius: 1.2rem;
            background: var(--accent);
            color: var(--on-accent);
            font-size: 1.5rem;
            font-weight: 600;
        }

        &__dots {
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        &__dot {
            width: 0.6rem;
            height: 0.6rem;
            border-radius: 50%;
            background: var(--track);
        }

        &__dot--on {
            width: 1.6rem;
            border-radius: 0.4rem;
            background: var(--accent);
        }
    }

    @keyframes tip-ripple {
        0% {
            opacity: 0;
            transform: scale(0.3);
        }

        25% {
            opacity: 1;
        }

        100% {
            opacity: 0;
            transform: scale(2.4);
        }
    }

    @keyframes tip-swipe {
        0%,
        12% {
            transform: translateX(0) rotate(0);
        }

        45%,
        62% {
            transform: translateX(4rem) rotate(3deg);
        }

        95%,
        100% {
            transform: translateX(0) rotate(0);
        }
    }

    @keyframes tip-wave {
        0%,
        40%,
        100% {
            background: rgba(255, 255, 255, 0.32);
            transform: scaleY(1);
        }

        15% {
            background: #fff;
            transform: scaleY(1.12);
        }
    }

    @keyframes tip-hop {
        0%,
        10% {
            transform: translate(0, 0);
        }

        18% {
            transform: translate(0, -1.4rem);
        }

        30%,
        42% {
            transform: translate(25.6rem, 0);
        }

        50% {
            transform: translate(25.6rem, -1.4rem);
        }

        62%,
        100% {
            transform: translate(0, 0);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .StartTips__card--swipe,
        .StartTips__rung i,
        .StartTips__chip--hot,
        .StartTips__tap i,
        .StartTips__tap b {
            animation: none;
        }
    }
</style>
