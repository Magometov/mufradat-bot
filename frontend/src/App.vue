<script setup lang="ts">
    // #region Imports
    // Types
    import type { IEntry } from './types/entry';
    import type { ITheme } from './types/theme';

    // Vue
    import { computed, onMounted, ref } from 'vue';

    // Composables
    import { useRun } from './composables/useRun';
    import { useTelegram } from './composables/useTelegram';

    // Components
    import RunController from './components/run/RunController.vue';
    import StartScreen from './components/start/StartScreen.vue';
    import UiButton from './components/ui/UiButton.vue';
    // #endregion

    // #region Data
    const API_URL = import.meta.env.VITE_API_URL ?? '';
    const ENTRIES_URL = `${API_URL}/api/v1/entries/`;
    const THEMES_URL = `${API_URL}/api/v1/themes/`;

    // Колода целиком: постраничности у эндпоинта нет намеренно, прогон — снимок.
    const entries = ref<IEntry[]>([]);
    const themes = ref<ITheme[]>([]);
    const isLoading = ref(true);
    const error = ref('');

    const { card, position, total, hasPrev, hasNext, restore, start, next, prev, finish } =
        useRun(entries);
    const { init } = useTelegram();
    // #endregion

    // #region Computed
    // Тема без карточек дала бы кнопку в пустой прогон, поэтому её на главной нет.
    const filledThemes = computed<ITheme[]>(() =>
        themes.value.filter((theme) =>
            entries.value.some((entry) => entry.themes.includes(theme.slug)),
        ),
    );
    // #endregion

    // #region Methods
    /**
     * Забирает колоду и темы и поднимает незакрытый прогон.
     *
     * Оба запроса уходят разом: они не зависят друг от друга, а главная нужна собранной.
     */
    async function fetchDeck(): Promise<void> {
        isLoading.value = true;
        error.value = '';

        try {
            const responses = await Promise.all([fetch(ENTRIES_URL), fetch(THEMES_URL)]);
            const failed = responses.find((response) => !response.ok);
            if (failed !== undefined) throw new Error(String(failed.status));

            const [deck, list] = await Promise.all(responses.map((response) => response.json()));

            entries.value = deck as IEntry[];
            themes.value = list as ITheme[];
            restore();
        } catch {
            error.value = 'Колода не загрузилась. Проверь связь и попробуй снова.';
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * Начинает прогон по всей колоде или по одной теме.
     */
    function handleStart(theme: string | null): void {
        const selected =
            theme === null
                ? entries.value
                : entries.value.filter((entry) => entry.themes.includes(theme));

        start(selected);
    }
    // #endregion

    // #region Lifecycle
    onMounted(() => {
        init();
        fetchDeck();
    });
    // #endregion
</script>

<template>
    <main :class="$style.App">
        <Transition name="fade" mode="out-in">
            <p v-if="isLoading" key="loading" :class="$style.App__note">Загружаю колоду…</p>

            <div v-else-if="error" key="error" :class="$style.App__error">
                <p :class="$style.App__note">{{ error }}</p>
                <UiButton @click="fetchDeck">Попробовать снова</UiButton>
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

            <StartScreen
                v-else
                key="start"
                :total="entries.length"
                :themes="filledThemes"
                @start="handleStart"
            />
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
