<script setup lang="ts">
    // #region Imports
    // Types
    import type { TVerdict } from '../../types/progress';
    import type { IRunCard, TRunKind, TSlide } from '../../types/run';

    // Vue
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

    // Composables
    import { useSwipe } from '../../composables/useSwipe';

    // Components
    import RunCard from './RunCard.vue';
    import RunControls from './RunControls.vue';
    import RunPill from './RunPill.vue';
    import UiButton from '../ui/UiButton.vue';

    // Icons
    import { X } from '@lucide/vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            card: IRunCard;
            /** Повторение оценивает, просмотр листает. */
            kind: TRunKind;
            /** Доля пройденного: в повторении её считает сеанс, в просмотре — место в колоде. */
            done: number;
            /** Что засчитала последняя оценка. Пусто — пилюли нет. */
            pill?: string;
            position?: number;
            total?: number;
            hasPrev?: boolean;
            hasNext?: boolean;
        }>(),
        { pill: '', position: 0, total: 0, hasPrev: false, hasNext: false },
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        know: [];
        forgot: [];
        cancel: [];
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
    // Без округления до целых: в длинном сеансе один ответ — это доли процента, и
    // округлённая полоса стояла бы на месте.
    const progress = computed<string>(() => `${(props.done * 100).toFixed(2)}%`);

    const isReview = computed<boolean>(() => props.kind === 'review');

    // Метка появляется по мере ухода: видно, что засчитается, ещё до того как отпустил.
    const mark = computed<TVerdict | ''>(() => {
        if (!isReview.value || direction.value === 0) return '';

        return direction.value > 0 ? 'know' : 'forgot';
    });
    // #endregion

    // #region Methods
    /**
     * Переворачивает текущую карточку. Переворачивать можно сколько угодно.
     */
    function handleFlip(): void {
        isFlipped.value = !isFlipped.value;
    }

    /**
     * Оценка карточки.
     */
    function handleRate(verdict: TVerdict): void {
        if (!isReview.value) return;

        slide.value = 'slide-forward';

        if (verdict === 'know') emit('know');
        else emit('forgot');
    }

    /**
     * Просит отменить последнюю оценку.
     */
    function handleCancel(): void {
        emit('cancel');
    }

    /**
     * Шаг назад по прогону: карточка уезжает вправо.
     */
    function handlePrev(): void {
        if (isReview.value || !props.hasPrev) return;

        slide.value = 'slide-back';
        emit('prev');
    }

    /**
     * Шаг вперёд по прогону: карточка уезжает влево.
     */
    function handleNext(): void {
        if (isReview.value || !props.hasNext) return;

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

            if (isReview.value) handleRate('forgot');
            else handlePrev();

            return;
        }

        if (event.key === 'ArrowRight') {
            event.preventDefault();

            if (isReview.value) handleRate('know');
            else handleNext();

            return;
        }

        if (!FLIP_KEYS.includes(event.key as (typeof FLIP_KEYS)[number])) return;
        if (event.target instanceof HTMLButtonElement) return;

        event.preventDefault();
        handleFlip();
    }
    // #endregion

    // #region Lifecycle
    // До переворота любой жест по карточке её переворачивает: мёртвых жестов не остаётся.
    const { direction } = useSwipe(stage, {
        tap: handleFlip,
        left: () => (isReview.value ? handleRate('forgot') : handleNext()),
        right: () => (isReview.value ? handleRate('know') : handlePrev()),
    });

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
            <!-- Карточки под верхней выглядывают снизу: видно, что колода не кончилась.
                 Живут в сцене, а не в карточке, иначе уезжали бы вместе с ней. -->
            <div
                :class="[$style.RunController__behind, $style['RunController__behind--far']]"
                aria-hidden="true"
            ></div>
            <div
                :class="[$style.RunController__behind, $style['RunController__behind--near']]"
                aria-hidden="true"
            ></div>

            <Transition :name="slide">
                <RunCard
                    :key="props.card.entry.id"
                    :card="props.card"
                    :is-flipped="isFlipped"
                    :mark="mark"
                />
            </Transition>
        </div>

        <div :class="$style.RunController__foot">
            <RunPill :text="props.pill" @cancel="handleCancel" />

            <RunControls
                :kind="props.kind"
                :position="props.position"
                :total="props.total"
                :has-prev="props.hasPrev"
                :has-next="props.hasNext"
                @know="handleRate('know')"
                @forgot="handleRate('forgot')"
                @prev="handlePrev"
                @next="handleNext"
                @finish="handleFinish"
            />
        </div>
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

        // Пилюля висит над подвалом, поэтому у него своё место в разметке.
        &__foot {
            position: relative;
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

        // Тон, а не тень: карточка шире слоёв, и в вырезах у её скруглённых углов любая
        // тень внутри стопки читается серым клином. Слои и так видно — они светлее фона.
        &__behind {
            position: absolute;
            border-radius: 2.4rem;
            background: var(--behind);
        }

        &__behind--far {
            top: 1.6rem;
            right: 2.6rem;
            bottom: 0;
            left: 2.6rem;
        }

        &__behind--near {
            top: 0.8rem;
            right: 1.4rem;
            bottom: 0.8rem;
            left: 1.4rem;
        }

        // Уезжающая и приезжающая карточки лежат здесь одновременно, поэтому высоту
        // держит сцена. По горизонтали она не обрезает: карточка ровно её ширины, и клип
        // срезал бы скругления ведущего края в тот же миг, как жест начался. Обрезает
        // весь экран — там край далеко и незаметен.
        &__stage {
            position: relative;
            flex: 1;
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
