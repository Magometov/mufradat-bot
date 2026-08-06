<script setup lang="ts">
    // #region Imports
    // Types
    import type { IRunCard, TSlide } from '../../types/run';

    // Vue
    import { ref, watch } from 'vue';

    // Components
    import RunCard from './RunCard.vue';
    import RunControls from './RunControls.vue';
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            card: IRunCard;
            position: number;
            total: number;
            hasPrev: boolean;
            hasNext: boolean;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        prev: [];
        next: [];
        finish: [];
    }>();
    // #endregion

    // #region Data
    // Сторона карточки живёт здесь: только контроллер знает, что карточка сменилась.
    const isFlipped = ref(false);
    // Направление уезда ставится до эмита: новая карточка придёт уже с нужным классом.
    const slide = ref<TSlide>('slide-forward');
    // #endregion

    // #region Methods
    /**
     * Переворачивает текущую карточку. Переворачивать можно сколько угодно.
     */
    function handleFlip(): void {
        isFlipped.value = !isFlipped.value;
    }

    /**
     * Шаг назад по прогону: карточка уезжает вправо.
     */
    function handlePrev(): void {
        slide.value = 'slide-back';
        emit('prev');
    }

    /**
     * Шаг вперёд по прогону: карточка уезжает влево.
     */
    function handleNext(): void {
        slide.value = 'slide-forward';
        emit('next');
    }

    /**
     * Бросает прогон и возвращает на начальный экран.
     */
    function handleFinish(): void {
        emit('finish');
    }
    // #endregion

    // #region Lifecycle
    // Новая карточка всегда приходит лицом вверх, иначе ответ виден до припоминания.
    watch(
        () => props.card.entry.id,
        () => {
            isFlipped.value = false;
        },
    );
    // #endregion
</script>

<template>
    <section :class="$style.RunController">
        <header :class="$style.RunController__bar">
            <UiButton variant="ghost" @click="handleFinish">Завершить</UiButton>
        </header>

        <div :class="$style.RunController__stage">
            <Transition :name="slide">
                <RunCard
                    :key="props.card.entry.id"
                    :card="props.card"
                    :is-flipped="isFlipped"
                    @flip="handleFlip"
                />
            </Transition>
        </div>

        <RunControls
            :position="props.position"
            :total="props.total"
            :has-prev="props.hasPrev"
            :has-next="props.hasNext"
            @prev="handlePrev"
            @next="handleNext"
            @finish="handleFinish"
        />
    </section>
</template>

<style module lang="scss">
    .RunController {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 1.6rem;

        &__bar {
            display: flex;
            justify-content: flex-end;
        }

        // Уезжающая и приезжающая карточки лежат здесь одновременно, поэтому высоту
        // держит сцена. Обрезка нужна, чтобы карточка не выезжала за края экрана.
        &__stage {
            position: relative;
            flex: 1;
            overflow: hidden;
        }
    }
</style>
