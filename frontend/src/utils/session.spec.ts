// #region Imports
// Types
import type { ISessionCard, TVerdict } from '../types/progress';

// Utils
import { GAP_AFTER_KNOW, GAP_AFTER_MISS, MIN_AHEAD, answer, isReversedAt } from './session';
import { shuffle } from './shuffle';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NEEDED = 2;
// Очередь, на которой доли остатка превращаются в заметные расстояния.
const LONG = 300;

/**
 * Карточка очереди: номер, уровень, счёт верных сторон, число промахов и сторона.
 */
function card(
    id: string,
    level: number | null = 0,
    step = 0,
    misses = 0,
    isReversed = false,
): ISessionCard {
    return { id, isReversed, level, step, misses };
}

/**
 * Та же карточка после возврата: сторона у неё уже перевёрнута.
 */
function returned(id: string, level: number | null = 0, step = 0, misses = 0): ISessionCard {
    return card(id, level, step, misses, true);
}

const ids = (queue: ISessionCard[]): string[] => queue.map((item) => item.id);

/**
 * Очередь заданной длины из ни разу не оценённых карточек.
 */
function queue(size = LONG): ISessionCard[] {
    return Array.from({ length: size }, (_, index) => card(`w${index + 1}`));
}

/**
 * На каком месте в новой очереди оказалась карточка.
 */
function placeOf(next: ISessionCard[], id: string): number {
    return ids(next).indexOf(id);
}

/**
 * Карточка очереди по номеру: место у неё разное, а содержимое проверяется всегда.
 */
function found(next: ISessionCard[], id: string): ISessionCard | undefined {
    return next.find((item) => item.id === id);
}

/**
 * Куда падает первая карточка очереди после оценки, много раз подряд.
 */
function places(head: ISessionCard, verdict: TVerdict, size = LONG): number[] {
    const tail = queue(size).slice(1);

    return Array.from({ length: 1500 }, () =>
        placeOf(answer([head, ...tail], verdict, NEEDED), head.id),
    );
}

/**
 * Средний зазор до возврата: место разбрасывается, поэтому проверяется среднее.
 */
function gapOf(head: ISessionCard, verdict: TVerdict, size = LONG): number {
    const drawn = places(head, verdict, size);

    return drawn.reduce((sum, value) => sum + value, 0) / drawn.length;
}

describe('сторона карточки', () => {
    it.each([
        [1, true],
        [2, false],
        [3, true],
        [4, false],
        [5, true],
    ])('ступень %i спрашивается своей стороной', (level, isReversed) => {
        expect(isReversedAt(level, 0)).toBe(isReversed);
    });

    it.each([[null], [0], [3], [4]])(
        'подтверждённая сторона ступени %s не спрашивается снова',
        (level) => {
            // Сеанс могли бросить между сторонами: вторая ждёт в следующем заходе.
            expect(isReversedAt(level, 1)).toBe(!isReversedAt(level, 0));
        },
    );

    it('новая карточка показывается арабской стороной', () => {
        // Русским вперёд её не вспомнить: слово ещё ни разу не видели.
        expect(isReversedAt(null, 0)).toBe(false);
    });

    it('возврат спрашивает слово другой стороной', () => {
        const once = answer(queue(), 'forgot', NEEDED);
        const twice = answer([card('w1', 0, 0, 1, true), ...queue().slice(1)], 'forgot', NEEDED);

        expect(found(once, 'w1')?.isReversed).toBe(true);
        expect(found(twice, 'w1')?.isReversed).toBe(false);
    });
});

describe('куда возвращается карточка', () => {
    it.each([
        [1, GAP_AFTER_MISS[0]!],
        [2, GAP_AFTER_MISS[1]!],
        [3, GAP_AFTER_MISS[2]!],
        [9, GAP_AFTER_MISS[2]!],
    ])('промах номер %i возвращает слово через свой зазор', (misses, gap) => {
        // Промахов больше, чем зазоров, — дальше последнего не отодвигает.
        expect(gapOf(card('w1', 0, 0, misses - 1), 'forgot')).toBeCloseTo(MIN_AHEAD + gap, -1);
    });

    it('вторая сторона слова, которое далось, уезжает дальше всякого промаха', () => {
        expect(gapOf(card('w1'), 'know')).toBeCloseTo(MIN_AHEAD + GAP_AFTER_KNOW, -1);
    });

    it('вспомнил после промаха — подтверждение спрашивается скорее, а не дальше', () => {
        expect(gapOf(card('w1', 0, 0, 1), 'know')).toBeCloseTo(MIN_AHEAD + GAP_AFTER_MISS[0]!, -1);
    });

    it('зазор не зависит от размера колоды', () => {
        // Память не знает, сколько слов в разделе: ей важно, сколько чужих прошло между
        // двумя показами. Доля остатка давала бы шесть карточек на полутора десятках.
        const small = gapOf(card('w1'), 'know', 150);
        const large = gapOf(card('w1'), 'know', 800);

        expect(Math.abs(small - large) / large).toBeLessThan(0.15);
    });

    it('места возврата разбросаны широко, а не жмутся к одному числу', () => {
        // Узкий разброс сбивает возвраты в кучу: за первым десятком новых слов идёт
        // десяток повторов подряд, и так на любой колоде.
        const drawn = places(card('w1'), 'know');

        expect(Math.min(...drawn)).toBeLessThan(MIN_AHEAD + GAP_AFTER_KNOW / 2);
        expect(Math.max(...drawn)).toBeGreaterThan(MIN_AHEAD + GAP_AFTER_KNOW * 2);
    });

    it('на короткой очереди зазор ужимается, а не упирается в конец', () => {
        // Иначе сеанс из полутора десятков слов распадается на круг новых и круг повторов.
        const short = gapOf(card('w1'), 'know', 20);

        expect(short).toBeLessThan(MIN_AHEAD + GAP_AFTER_KNOW / 2);
        expect(short).toBeGreaterThan(MIN_AHEAD);
    });

    it('ближе порога слово не возвращается даже в короткой очереди', () => {
        expect(Math.min(...places(card('w1', 0, 0, 1), 'forgot', 20))).toBeGreaterThanOrEqual(
            MIN_AHEAD,
        );
    });

    it('дальше конца очереди слово не уезжает', () => {
        expect(ids(answer([card('w1'), card('w2'), card('w3')], 'know', NEEDED))).toEqual([
            'w2',
            'w3',
            'w1',
        ]);
    });

    it('в короткой очереди возврат не роняет карточки', () => {
        expect(answer(queue(4), 'forgot', NEEDED)).toHaveLength(4);
    });

    it('последняя карточка, оценённая промахом, остаётся одна', () => {
        expect(ids(answer([card('w1')], 'forgot', NEEDED))).toEqual(['w1']);
    });
});

describe('очередь сеанса', () => {
    it('промахи помнятся в самой карточке', () => {
        const next = answer(queue(), 'forgot', NEEDED);

        expect(found(next, 'w1')).toEqual(returned('w1', 0, 0, 1));
    });

    it('первая верная сторона в изучении только считается', () => {
        const next = answer(queue(), 'know', NEEDED);

        expect(found(next, 'w1')).toEqual(returned('w1', 0, 1, 0));
    });

    it('вторая верная сторона закрывает карточку', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'know', NEEDED);

        expect(ids(next)).toEqual(['w2']);
    });

    it('промах обнуляет счёт верных сторон', () => {
        const next = answer([card('w1', 0, 1), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(returned('w1', 0, 0, 1));
    });

    it('знакомая карточка ждёт вторую сторону, как и всякая другая', () => {
        const next = answer([card('w1', 3), ...queue().slice(1)], 'know', NEEDED);

        expect(found(next, 'w1')).toEqual(returned('w1', 3, 1, 0));
    });

    it('забытая знакомая падает в изучение и возвращается', () => {
        const next = answer([card('w1', 4), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(returned('w1', 0, 0, 1));
    });

    it('узнанная с первого взгляда возвращается за второй стороной', () => {
        const next = answer([card('w1', null), ...queue().slice(1)], 'know', NEEDED);

        expect(found(next, 'w1')).toEqual(returned('w1', null, 1, 0));
    });

    it('незнакомая новая падает в изучение и возвращается', () => {
        const next = answer([card('w1', null), card('w2')], 'forgot', NEEDED);

        expect(next.at(-1)).toEqual(returned('w1', 0, 0, 1));
    });

    it('последняя закрытая карточка кончает сеанс', () => {
        expect(answer([card('w1', 2, 1)], 'know', NEEDED)).toEqual([]);
    });

    it('пустую очередь оценивать нечем', () => {
        expect(answer([], 'know', NEEDED)).toEqual([]);
    });

    it('число верных сторон задаётся снаружи, а не зашито', () => {
        const next = answer([card('w1', 0, 1), ...queue().slice(1)], 'know', 3);

        expect(found(next, 'w1')).toEqual(returned('w1', 0, 2, 0));
    });
});

describe('сеанс целиком', () => {
    // Столько карточек человек проходит за длинный вечер: на этом размере и видно,
    // сходится ли очередь вообще.
    const BIG = 250;
    // Потолок нажатий: сеанс, который в него упёрся, не кончается сам.
    const ENDLESS = BIG * 20;

    /**
     * Прогоняет сеанс до конца, отвечая по правилу. Отдаёт, чем каждую карточку
     * спрашивали и сколько всего было нажатий.
     */
    function play(verdictAt: (shown: number) => TVerdict): {
        sides: Map<string, Set<boolean>>;
        presses: number;
    } {
        const sides = new Map<string, Set<boolean>>();
        let queue = shuffle(Array.from({ length: BIG }, (_, index) => card(`w${index + 1}`, null)));
        let presses = 0;

        while (queue.length > 0 && presses < ENDLESS) {
            const shown = queue[0]!;
            const seen = sides.get(shown.id) ?? new Set<boolean>();

            seen.add(shown.isReversed);
            sides.set(shown.id, seen);

            queue = answer(queue, verdictAt(seen.size), NEEDED);
            presses += 1;
        }

        return { sides, presses };
    }

    it('сеанс на две с половиной сотни карточек кончается сам', () => {
        const { sides, presses } = play(() => 'know');

        expect(presses).toBe(BIG * NEEDED);
        expect(sides.size).toBe(BIG);
    });

    it('каждая карточка спрашивается обеими сторонами', () => {
        // Иначе лестница растёт вхолостую: узнать написанное легче, чем вспомнить самому.
        const { sides } = play(() => 'know');

        expect([...sides.values()].every((seen) => seen.size === 2)).toBe(true);
    });

    it('промахи сеанс не зацикливают', () => {
        // Первый показ каждой карточки — промах: очередь от этого растёт, но сходится.
        const { sides, presses } = play((shown) => (shown === 1 ? 'forgot' : 'know'));

        expect(presses).toBeLessThan(ENDLESS);
        expect(sides.size).toBe(BIG);
    });
});
