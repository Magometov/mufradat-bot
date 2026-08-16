<script setup lang="ts">
    // #region Imports
    // Utils
    import { isHintSeen, markHintSeen } from '../../utils/storage';

    // Vue
    import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

    // Composables
    import { useAppearance } from '../../composables/useAppearance';

    // Components
    import UiButton from '../ui/UiButton.vue';

    // Icons
    import { Moon, Sun } from '@lucide/vue';
    // #endregion

    // #region Data
    // Возникнув разом с экраном, подсказка читалась бы как часть интерфейса, а не как
    // замечание. Полсекунды хватает, чтобы она была именно замечанием.
    const DELAY = 500;

    // Столько висит, если её не трогают.
    const LIFETIME = 7000;

    const { appearance, toggle } = useAppearance();
    const isHintVisible = ref(false);

    let showTimer = 0;
    let hideTimer = 0;
    // #endregion

    // #region Computed
    const icon = computed(() => (appearance.value === 'dark' ? Sun : Moon));

    const label = computed<string>(() =>
        appearance.value === 'dark' ? 'Включить светлое оформление' : 'Включить тёмное оформление',
    );
    // #endregion

    // #region Methods
    /**
     * Убирает подсказку и перестаёт слушать экран.
     */
    function hideHint(): void {
        isHintVisible.value = false;
        window.clearTimeout(hideTimer);
        document.removeEventListener('pointerdown', hideHint);
    }

    /**
     * Показывает подсказку и сразу отмечает её показанной.
     *
     * Отметка в момент показа, а не закрытия: иначе закрывшему приложение через секунду
     * она вылезала бы снова и снова.
     */
    function showHint(): void {
        markHintSeen();
        isHintVisible.value = true;
        hideTimer = window.setTimeout(hideHint, LIFETIME);
        document.addEventListener('pointerdown', hideHint);
    }

    /**
     * Переключает оформление. Подсказка после этого уже ни к чему.
     */
    function handleToggle(): void {
        hideHint();
        toggle();
    }
    // #endregion

    // #region Lifecycle
    onMounted(() => {
        if (isHintSeen()) return;

        showTimer = window.setTimeout(showHint, DELAY);
    });

    onBeforeUnmount(() => {
        window.clearTimeout(showTimer);
        hideHint();
    });
    // #endregion
</script>

<template>
    <div :class="$style.StartAppearance">
        <UiButton
            :class="$style.StartAppearance__button"
            variant="plain"
            :aria-label="label"
            @click="handleToggle"
        >
            <component :is="icon" :size="20" />
        </UiButton>

        <Transition name="fade">
            <!-- Висит абсолютно: разметку не двигает и кнопки режима не накрывает. -->
            <p v-if="isHintVisible" :class="$style.StartAppearance__hint" role="status">
                Здесь меняется тема
            </p>
        </Transition>
    </div>
</template>

<style module lang="scss">
    .StartAppearance {
        position: relative;
        display: flex;
        justify-content: flex-end;

        &__button {
            width: 4.4rem;
            height: 4.4rem;
            padding: 0;
            border-radius: 50%;
            color: var(--muted);
        }

        &__hint {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 1.2rem;
            padding: 1.2rem 1.6rem;
            border-radius: 1.4rem;
            background: var(--surface);
            box-shadow: var(--lift);
            font-size: 1.5rem;
            white-space: nowrap;
            pointer-events: none;
        }

        // Уголок к кнопке — повёрнутый квадрат того же цвета.
        &__hint::before {
            content: '';
            position: absolute;
            top: -0.5rem;
            right: 1.6rem;
            width: 1.2rem;
            height: 1.2rem;
            border-radius: 2px;
            background: var(--surface);
            transform: rotate(45deg);
        }
    }
</style>
