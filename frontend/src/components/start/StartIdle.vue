<script setup lang="ts">
    // #region Imports
    // Components
    import UiButton from '../ui/UiButton.vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            title: string;
            /** Когда придёт ближайшая карточка раздела. Пусто — карточек в нём нет вовсе. */
            next: string;
            /** Сколько всего карточек в разделе. */
            total: number;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        view: [];
        back: [];
    }>();
    // #endregion
</script>

<template>
    <section :class="$style.StartIdle">
        <header :class="$style.StartIdle__head">
            <UiButton variant="ghost" @click="emit('back')">←</UiButton>

            <h2 :class="$style.StartIdle__title">{{ props.title }}</h2>
        </header>

        <div :class="$style.StartIdle__body">
            <p :class="$style.StartIdle__note">
                Здесь на сегодня нечего повторять.
                <template v-if="props.next">
                    <br />
                    Ближайшее слово — <b>{{ props.next }}</b
                    >.
                </template>
            </p>

            <UiButton variant="plain" @click="emit('view')"> Посмотреть раздел целиком </UiButton>

            <p :class="$style.StartIdle__hint">{{ props.total }} карточек, без оценок</p>
        </div>
    </section>
</template>

<style module lang="scss">
    .StartIdle {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 2rem;

        &__head {
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        &__title {
            font-size: 1.9rem;
            font-weight: 600;
        }

        &__body {
            display: flex;
            flex: 1;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.6rem;
        }

        &__note {
            color: var(--muted);
            text-align: center;

            b {
                color: var(--ink);
                font-weight: 600;
            }
        }

        &__hint {
            color: var(--muted);
            font-size: 1.3rem;
        }
    }
</style>
