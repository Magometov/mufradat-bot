<script setup lang="ts">
    // #region Imports
    // Types
    import type { IEntry } from './types/entry';
    import type { TVerdict } from './types/progress';
    import type { ITheme } from './types/theme';

    // Vue
    import { computed, onMounted, ref, watch } from 'vue';

    // Utils
    import { API_URL } from './utils/api';
    import { countDue, nextDueAt, soonText, summarize } from './utils/due';
    import { MODE_TITLES } from './utils/modes';
    import { dayWord } from './utils/plural';
    import { buildPortion } from './utils/portion';
    import { days } from './utils/predict';
    import { logVisit } from './utils/visit';

    // Composables
    import { useProgress } from './composables/useProgress';
    import { useRun } from './composables/useRun';
    import { useSelection } from './composables/useSelection';
    import { useSession } from './composables/useSession';
    import { useTelegram } from './composables/useTelegram';

    // Components
    import RunController from './components/run/RunController.vue';
    import RunDone from './components/run/RunDone.vue';
    import StartMode from './components/start/StartMode.vue';
    import StartSections from './components/start/StartSections.vue';
    import UiButton from './components/ui/UiButton.vue';
    // #endregion

    // #region Data
    const CARDS_URL = `${API_URL}/api/v1/cards/`;
    const THEMES_URL = `${API_URL}/api/v1/themes/`;
    const VISITS_URL = `${API_URL}/api/v1/visits/`;

    // Колода целиком: постраничности у эндпоинта нет намеренно, прогон — снимок.
    const entries = ref<IEntry[]>([]);
    const themes = ref<ITheme[]>([]);
    const isLoading = ref(true);
    const error = ref('');
    // Что засчитала последняя оценка: текст пилюли с отменой.
    const pill = ref('');
    // Просмотр колоды — сегодняшнее приложение: там нет ни оценок, ни цифр.
    const isViewing = ref(false);
    // Итог закрытого сеанса. Пусто — экрана конца нет.
    const summary = ref('');

    const { initData, init } = useTelegram();
    const { enabled, rules, progress, now, fetchState, record, cancelLast, flush } =
        useProgress(initData);
    const needed = computed<number>(() => rules.value?.needed ?? 2);

    const { card, position, total, hasPrev, hasNext, restore, start, next, prev, finish } =
        useRun(entries);
    const session = useSession(entries, needed);
    const { mode, sections, choose, cardsFor, reset } = useSelection(entries, themes);
    // #endregion

    // #region Computed
    const modeTitle = computed<string>(() => (mode.value === null ? '' : MODE_TITLES[mode.value]));

    // Повторение идёт по расписанию, просмотр — по колоде: у каждого свой прогон.
    const isScheduled = computed<boolean>(() => enabled.value && !isViewing.value);
    const isReview = computed<boolean>(() => isScheduled.value && session.card.value !== null);
    const shownCard = computed(() => (isReview.value ? session.card.value : card.value));
    const done = computed<number>(() =>
        isReview.value ? session.done.value : position.value / total.value,
    );

    // Сколько на сегодня: по всей колоде, по выбранному режиму и по каждому разделу.
    const dueTotal = computed<number>(() => countDue(entries.value, progress.value, now()));

    const dueMode = computed<number>(() => countDue(cardsFor(null), progress.value, now()));

    const dueByTheme = computed<Map<string, number>>(
        () =>
            new Map(
                sections.value.map((section) => [
                    section.slug,
                    countDue(cardsFor(section.slug), progress.value, now()),
                ]),
            ),
    );

    // Когда придёт ближайшая карточка, если на сегодня ничего нет.
    const nextWord = computed<string>(() => {
        const at = nextDueAt(entries.value, progress.value);

        return at === null ? '' : soonText(at, now());
    });
    // #endregion

    // #region Methods
    /**
     * Забирает колоду, темы и прогресс и поднимает незакрытый прогон.
     *
     * Все три запроса уходят разом: они не зависят друг от друга, а главная нужна собранной.
     */
    async function fetchDeck(): Promise<void> {
        isLoading.value = true;
        error.value = '';

        try {
            const [deck, list] = await Promise.all([
                fetch(CARDS_URL),
                fetch(THEMES_URL),
                fetchState(),
            ]);

            if (!deck.ok || !list.ok) throw new Error('колода не пришла');

            entries.value = (await deck.json()) as IEntry[];
            themes.value = (await list.json()) as ITheme[];

            if (!enabled.value) restore();
        } catch {
            error.value = 'Колода не загрузилась. Проверь связь и попробуй снова.';
        } finally {
            isLoading.value = false;
        }
    }

    /**
     * Начинает прогон по разделу: с расписанием — сегодняшней порцией, без него — целиком.
     */
    function handleStart(theme: string | null): void {
        const selected = cardsFor(theme);

        if (!isScheduled.value) {
            start(selected);
            return;
        }

        // Потолков в разделе нет: пришёл сам — получай всё, что на сегодня.
        summary.value = '';
        session.start(buildPortion(selected, progress.value, now(), null), progress.value);
    }

    /**
     * Ежедневная доза по всей колоде: с потолком, в отличие от захода в раздел.
     */
    function handleRepeat(): void {
        if (rules.value === null) return;

        const limits = {
            sessionLimit: rules.value.sessionLimit,
            newLimit: rules.value.newLimit,
        };

        summary.value = '';
        session.start(buildPortion(entries.value, progress.value, now(), limits), progress.value);
    }

    /**
     * Уводит в просмотр колоды: там приложение работает как до расписания.
     */
    function handleView(): void {
        isViewing.value = true;
        reset();
    }

    /**
     * Записывает оценку и показывает, куда уехала карточка.
     */
    function handleRate(verdict: TVerdict): void {
        const first = session.card.value;
        if (first === null) return;

        const state = record(first.entry.id, verdict);
        session.answer(verdict);

        if (state === null || verdict === 'forgot' || rules.value === null) {
            pill.value = '';
            return;
        }

        const span = days(state.level, rules.value);
        pill.value = `через ${span} ${dayWord(span)}`;
    }

    /**
     * Отменяет последнюю оценку, пока она не уехала на сервер.
     */
    function handleCancel(): void {
        pill.value = '';

        if (cancelLast()) session.undo();
    }

    /**
     * Закрывает прогон: оценённое уезжает сразу, не дожидаясь таймера.
     */
    function handleFinish(): void {
        pill.value = '';

        if (isReview.value) {
            session.finish();
            void flush();
            return;
        }

        finish();
    }

    /**
     * Уходит с экрана конца сеанса.
     */
    function handleHome(): void {
        summary.value = '';
        isViewing.value = false;
        reset();
    }
    // #endregion

    // #region Lifecycle
    // Очередь опустела — сеанс закончился сам, и его итог занимает место карточки.
    watch(session.left, (left, was) => {
        if (left !== 0 || was === 0 || !isScheduled.value) return;

        summary.value = summarize(session.ids.value, progress.value, now());
        void flush();
    });

    onMounted(() => {
        init();
        logVisit(VISITS_URL, initData);
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
                v-else-if="shownCard"
                key="run"
                :card="shownCard"
                :kind="isReview ? 'review' : 'view'"
                :done="done"
                :pill="pill"
                :position="position"
                :total="total"
                :has-prev="hasPrev"
                :has-next="hasNext"
                @know="handleRate('know')"
                @forgot="handleRate('forgot')"
                @cancel="handleCancel"
                @prev="prev"
                @next="next"
                @finish="handleFinish"
            />

            <RunDone
                v-else-if="summary"
                key="done"
                :summary="summary"
                :left="dueTotal"
                @more="handleRepeat"
                @home="handleHome"
            />

            <StartSections
                v-else-if="mode"
                key="sections"
                :title="modeTitle"
                :sections="sections"
                :due="dueByTheme"
                :due-all="dueMode"
                :is-review="isScheduled"
                @select="handleStart"
                @back="reset"
            />

            <StartMode
                v-else
                key="mode"
                :total="entries.length"
                :is-review="isScheduled"
                :due="dueTotal"
                :next="nextWord"
                @select="choose"
                @repeat="handleRepeat"
                @view="handleView"
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
            color: var(--muted);
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
