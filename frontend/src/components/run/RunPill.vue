<script setup lang="ts">
    // #region Imports
    // Vue
    import { onBeforeUnmount, ref, watch } from 'vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            /** Что засчитали: «через 7 дней». Пусто — пилюли нет. */
            text: string;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        cancel: [];
    }>();
    // #endregion

    // #region Data
    // Тост живёт недолго: он подтверждает нажатие, а не учит.
    const LIFETIME = 2500;

    const isVisible = ref(false);

    let timer = 0;
    // #endregion

    // #region Methods
    /**
     * Просит отменить оценку и убирает пилюлю.
     */
    function handleCancel(): void {
        isVisible.value = false;
        emit('cancel');
    }
    // #endregion

    // #region Lifecycle
    watch(
        () => props.text,
        (text) => {
            window.clearTimeout(timer);
            isVisible.value = text !== '';

            if (text === '') return;

            timer = window.setTimeout(() => (isVisible.value = false), LIFETIME);
        },
    );

    onBeforeUnmount(() => window.clearTimeout(timer));
    // #endregion
</script>

<template>
    <Transition name="fade">
        <p v-if="isVisible" :class="$style.RunPill" role="status">
            <span>{{ props.text }}</span>
            <button :class="$style.RunPill__cancel" type="button" @click="handleCancel">
                Отменить
            </button>
        </p>
    </Transition>
</template>

<style module lang="scss">
    .RunPill {
        position: absolute;
        bottom: 0;
        left: 50%;
        display: flex;
        align-items: center;
        gap: 1.2rem;
        padding: 0.8rem 1.4rem;
        border-radius: 2.4rem;
        background: var(--surface);
        box-shadow: var(--lift-sm);
        color: var(--muted);
        font-size: 1.4rem;
        white-space: nowrap;
        transform: translateX(-50%);

        &__cancel {
            padding: 0;
            border: 0;
            background: none;
            color: var(--accent);
            font-size: 1.4rem;
            font-weight: 600;
            cursor: pointer;
        }
    }
</style>
