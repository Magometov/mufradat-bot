<script setup lang="ts">
    // #region Imports
    // Types
    import type { IRunCard, TSlide } from '../../types/run';

    // Vue
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

    // Composables
    import { useSwipe } from '../../composables/useSwipe';

    // Components
    import RunCard from './RunCard.vue';
    import RunControls from './RunControls.vue';
    import UiButton from '../ui/UiButton.vue';

    // Icons
    import { X } from '@lucide/vue';
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
    const stage = ref<HTMLElement | null>(null);

    // Клавиши, которые переворачивают карточку. Пробел и Enter — то же, что нажатие.
    const FLIP_KEYS = [' ', 'Enter'] as const;
    // #endregion

    // #region Computed
    // Полоса отвечает на «сколько осталось», счётчик внизу — на «где я именно».
    const progress = computed<string>(() => `${(props.position / props.total) * 100}%`);
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
        if (!props.hasPrev) return;

        slide.value = 'slide-back';
        emit('prev');
    }

    /**
     * Шаг вперёд по прогону: карточка уезжает влево.
     */
    function handleNext(): void {
        if (!props.hasNext) return;

        slide.value = 'slide-forward';
        emit('next');
    }

    /**
     * Бросает прогон и возвращает на начальный экран.
     */
    function handleFinish(): void {
        emit('finish');
    }

    /**
     * Управление с клавиатуры: стрелки листают, пробел и Enter переворачивают.
     *
     * Обработчик один на окно, а не на карточке: тогда листать можно, не наводя на неё
     * фокус. Пробел и Enter при фокусе на кнопке не перехватываются — там это нажатие
     * самой кнопки, и подменять его нельзя.
     */
    function onKeydown(event: KeyboardEvent): void {
        if (event.altKey || event.ctrlKey || event.metaKey) return;

        if (event.key === 'ArrowLeft') {
            event.preventDefault();
            handlePrev();
            return;
        }

        if (event.key === 'ArrowRight') {
            event.preventDefault();
            handleNext();
            return;
        }

        if (!FLIP_KEYS.includes(event.key as (typeof FLIP_KEYS)[number])) return;
        if (event.target instanceof HTMLButtonElement) return;

        event.preventDefault();
        handleFlip();
    }
    // #endregion

    // #region Lifecycle
    useSwipe(stage, { tap: handleFlip, left: handleNext, right: handlePrev });

    onMounted(() => window.addEventListener('keydown', onKeydown));
    onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown));

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
            <span :class="$style.RunController__track">
                <i :class="$style.RunController__fill" :style="{ width: progress }"></i>
            </span>

            <UiButton variant="ghost" aria-label="Завершить прогон" @click="handleFinish">
                <X :size="22" />
            </UiButton>
        </header>

        <div ref="stage" :class="$style.RunController__stage">
            <Transition :name="slide">
                <RunCard :key="props.card.entry.id" :card="props.card" :is-flipped="isFlipped" />
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
            align-items: center;
            gap: 1.8rem;
        }

        &__track {
            flex: 1;
            height: 4px;
            border-radius: 2px;
            background: var(--track);
            overflow: hidden;
        }

        &__fill {
            display: block;
            height: 100%;
            border-radius: 2px;
            background: var(--accent);
            transition: width 0.26s ease;
        }

        // Уезжающая и приезжающая карточки лежат здесь одновременно, поэтому высоту
        // держит сцена. Обрезка нужна, чтобы карточка не выезжала за края экрана.
        &__stage {
            position: relative;
            flex: 1;
            overflow: hidden;
            // Горизонталь разбираем сами, вертикаль оставляем браузеру и клиенту:
            // иначе сломается и прокрутка длинной карточки, и жесты Telegram.
            touch-action: pan-y;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .RunController__fill {
            transition: none;
        }
    }
</style>
