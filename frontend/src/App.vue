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
    import { countDue, nextDueAt, pillText, soonText, summarize } from './utils/due';
    import { MODE_TITLES } from './utils/modes';
    import { buildPortion } from './utils/portion';
    import { isTipsSeen, markTipsSeen } from './utils/storage';
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
    import StartIdle from './components/start/StartIdle.vue';
    import StartMode from './components/start/StartMode.vue';
    import StartSections from './components/start/StartSections.vue';
    import StartTips from './components/start/StartTips.vue';
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
    // Раздел, в котором на сегодня пусто: показываем, когда ждать, и выход в просмотр.
    const idle = ref<string | null>(null);
    // Подсказки: сами всходят один раз, дальше — по кнопке «?».
    const isTipsOpen = ref(false);

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

    // То же для пустого раздела: там ждут ближайшую именно его карточку.
    const idleCards = computed<IEntry[]>(() => (idle.value === null ? [] : cardsFor(idle.value)));

    const idleNext = computed<string>(() => {
        const at = nextDueAt(idleCards.value, progress.value);

        return at === null ? '' : soonText(at, now());
    });

    const idleTitle = computed<string>(
        () =>
            sections.value.find((section) => section.slug === idle.value)?.name ?? modeTitle.value,
    );
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
        const portion = buildPortion(selected, progress.value, now(), null);

        // Пустой сеанс не открываем: вместо него экран с ближайшим сроком.
        if (portion.length === 0) {
            idle.value = theme;
            return;
        }

        summary.value = '';
        session.start(portion, progress.value);
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

        // Сеанс кончился сам — показываем итог. По опустевшей очереди этого делать нельзя:
        // крестик опустошает её точно так же, а из него человек хочет уйти, а не читать.
        if (session.left.value === 0) {
            summary.value = summarize(session.ids.value, progress.value, now());
            void flush();
        }

        pill.value = pillText(state, rules.value);
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

    /**
     * Закрывает подсказки и помнит, что их видели.
     */
    function handleTipsClose(): void {
        isTipsOpen.value = false;
        markTipsSeen();
    }

    /**
     * Смотрит раздел, в котором на сегодня пусто: расписание при этом не участвует.
     */
    function handleIdleView(): void {
        isViewing.value = true;
        start(idleCards.value);
        idle.value = null;
    }
    // #endregion

    // #region Lifecycle
    // Подсказки про расписание нужны только тому, у кого расписание есть. Ссылка из
    // бота открывает их и повторно: человек пришёл именно за ними.
    watch(enabled, (isOn) => {
        if (!isOn) return;

        if (!isTipsSeen() || window.location.hash.includes('tips')) isTipsOpen.value = true;
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

            <StartIdle
                v-else-if="idle !== null"
                key="idle"
                :title="idleTitle"
                :next="idleNext"
                :total="idleCards.length"
                @view="handleIdleView"
                @back="idle = null"
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

            <!-- Ключ разный для повторения и просмотра: переход играет на смене ключа, а
                 не свойств, иначе первый экран подменялся бы рывком. -->
            <StartMode
                v-else
                :key="isViewing ? 'mode-view' : 'mode-review'"
                :total="entries.length"
                :is-review="isScheduled"
                :due="dueTotal"
                :next="nextWord"
                :can-back="isViewing"
                @select="choose"
                @repeat="handleRepeat"
                @view="handleView"
                @back="isViewing = false"
                @tips="isTipsOpen = true"
            />
        </Transition>

        <StartTips v-if="isTipsOpen" :rules="rules" @close="handleTipsClose" />
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
