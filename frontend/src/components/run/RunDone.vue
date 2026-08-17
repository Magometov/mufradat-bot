<script setup lang="ts">
    // #region Imports
    // Components
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            /** Что стало с карточками сеанса: «8 слов вернутся через неделю». */
            summary: string;
            /** Сколько ещё назначено на сегодня. Нуль — брать больше нечего. */
            left?: number;
        }>(),
        { left: 0 },
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        more: [];
        home: [];
    }>();
    // #endregion
</script>

<template>
    <section :class="$style.RunDone">
        <div :class="$style.RunDone__stack" aria-hidden="true">
            <div :class="[$style.RunDone__card, $style['RunDone__card--back']]"></div>
            <div :class="[$style.RunDone__card, $style['RunDone__card--front']]">
                <span :class="$style.RunDone__title" dir="rtl" lang="ar">مفردات</span>
            </div>
        </div>

        <h2 :class="$style.RunDone__head">{{ props.left > 0 ? 'Готово' : 'На сегодня всё' }}</h2>

        <p :class="$style.RunDone__note">{{ props.summary }}</p>

        <div :class="$style.RunDone__choice">
            <UiButton v-if="props.left > 0" variant="accent" @click="emit('more')">
                Продолжить
            </UiButton>

            <UiButton variant="plain" @click="emit('home')">На главную</UiButton>
        </div>
    </section>
</template>

<style module lang="scss">
    .RunDone {
        display: flex;
        flex: 1;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2rem;

        &__stack {
            position: relative;
            width: 100%;
            height: 16rem;
        }

        &__card {
            position: absolute;
            top: 0;
            left: 50%;
            border-radius: 1.8rem;
            background: var(--behind);
        }

        &__card--back {
            width: 12rem;
            height: 15rem;
            margin-left: -6rem;
            transform: rotate(-6deg);
        }

        &__card--front {
            display: flex;
            width: 13rem;
            height: 15rem;
            align-items: center;
            justify-content: center;
            margin-left: -6.5rem;
            background: var(--surface);
        }

        &__title {
            font-family: var(--font-arabic);
            font-size: 2.6rem;
            line-height: 1.7;
        }

        &__head {
            font-size: 2rem;
            font-weight: 700;
        }

        &__note {
            color: var(--muted);
            text-align: center;
        }

        &__choice {
            display: flex;
            width: 100%;
            flex-direction: column;
            gap: 1.2rem;
        }
    }
</style>
