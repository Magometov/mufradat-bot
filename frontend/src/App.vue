<script setup lang="ts">
    // #region Imports
    // Types
    import type { IEntry } from './types/entry';

    // Vue
    import { onMounted, ref } from 'vue';

    // Composables
    import { useRun } from './composables/useRun';
    import { useTelegram } from './composables/useTelegram';

    // Components
    import RunController from './components/run/RunController.vue';
    import StartScreen from './components/start/StartScreen.vue';
    import UiButton from './components/ui/UiButton.vue';
    // #endregion

    // #region Data
    const ENTRIES_URL = `${import.meta.env.VITE_API_URL ?? ''}/api/v1/entries/`;

    // Колода целиком: постраничности у эндпоинта нет намеренно, прогон — снимок.
    const entries = ref<IEntry[]>([]);
    const isLoading = ref(true);
    const error = ref('');

    const { card, position, total, hasPrev, hasNext, restore, start, next, prev, finish } =
        useRun(entries);
    const { init } = useTelegram();
    // #endregion

    // #region Methods
    /**
     * Забирает колоду одним запросом и поднимает незакрытый прогон.
     */
    async function fetchEntries(): Promise<void> {
        isLoading.value = true;
        error.value = '';

        try {
            const response = await fetch(ENTRIES_URL);
            if (!response.ok) throw new Error(String(response.status));

            entries.value = (await response.json()) as IEntry[];
            restore();
        } catch {
            error.value = 'Колода не загрузилась. Проверь связь и попробуй снова.';
        } finally {
            isLoading.value = false;
        }
    }
    // #endregion

    // #region Lifecycle
    onMounted(() => {
        init();
        fetchEntries();
    });
    // #endregion
</script>

<template>
    <main :class="$style.App">
        <Transition name="fade" mode="out-in">
            <p v-if="isLoading" key="loading" :class="$style.App__note">Загружаю колоду…</p>

            <div v-else-if="error" key="error" :class="$style.App__error">
                <p :class="$style.App__note">{{ error }}</p>
                <UiButton @click="fetchEntries">Попробовать снова</UiButton>
            </div>

            <RunController
                v-else-if="card"
                key="run"
                :card="card"
                :position="position"
                :total="total"
                :has-prev="hasPrev"
                :has-next="hasNext"
                @prev="prev"
                @next="next"
                @finish="finish"
            />

            <StartScreen v-else key="start" :total="entries.length" @start="start" />
        </Transition>
    </main>
</template>

<style module lang="scss">
    .App {
        display: flex;
        flex-direction: column;
        min-height: 100dvh;
        max-width: 52rem;
        margin: 0 auto;
        padding: calc(1.6rem + env(safe-area-inset-top)) 1.6rem
            calc(1.6rem + env(safe-area-inset-bottom));

        &__note {
            color: var(--base-500);
            text-align: center;
        }

        &__error {
            display: flex;
            flex: 1;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2rem;
        }
    }
</style>
