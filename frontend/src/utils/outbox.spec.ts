// #region Imports
// Types
import type { IEntry } from '../types/entry';
import type { IAnswer, IProgress, IRules, TVerdict } from '../types/progress';

// Utils
import { IDLE_PAUSE, PAUSE_DEFAULT, PAUSE_LONGEST, isTimeToSend, pauseFor, replay } from './outbox';
import { dueCards } from './due';

// Vitest
import { describe, expect, it } from 'vitest';
// #endregion

const NOW = Date.parse('2026-08-19T12:00:00.000Z');
const DAY = 86_400_000;
const BATCH = 100;

const rules: IRules = {
    ladder: [1, 3, 7, 16, 35, 90, 180],
    jitter: 10,
    firstSightLevel: 3,
    needed: 2,
    lapseDrop: 2,
    answersLimit: BATCH,
};

/**
 * Оценка, какой она лежит в очереди: время нажатия строкой, как его шлёт приложение.
 */
function answer(id: string, verdict: TVerdict, at = NOW): IAnswer {
    return { card_id: id, verdict, answered_at: new Date(at).toISOString() };
}

/**
 * Состояние карточки на сервере.
 */
function state(level: number, dueAt: number, step = 0, lapses = 0, lapsedFrom = 0): IProgress {
    return { level, step, lapses, lapsedFrom, dueAt };
}

/**
 * Карточка колоды: для сборки порции важен только номер.
 */
function entry(id: string): IEntry {
    return {
        id,
        arabic: 'كِتَاب',
        translation_ru: 'книга',
        transliteration: '',
        is_word: true,
        image: null,
        image_width: null,
        image_height: null,
        themes: ['numbers'],
    };
}

describe('прогресс с неуехавшими оценками', () => {
    it('пустая очередь отдаёт состояния сервера как есть', () => {
        const server = new Map([['w1', state(3, NOW + DAY)]]);

        expect(replay(server, [], rules)).toBe(server);
    });

    it('без правил очередь не разбирается', () => {
        // Правила ещё не приехали: считать по ним срок нечем.
        const server = new Map([['w1', state(3, NOW + DAY)]]);

        expect(replay(server, [answer('w1', 'know')], null)).toBe(server);
    });

    it('оценки применяются по порядку, а последняя закрывает карточку', () => {
        const server = new Map([['w1', state(2, NOW - DAY)]]);
        const queue = [answer('w1', 'know'), answer('w1', 'know', NOW + 20_000)];

        const card = replay(server, queue, rules).get('w1');

        // Третья ступень — семь дней от нажатия, закрывшего карточку.
        expect(card).toEqual(state(3, NOW + 20_000 + 7 * DAY));
    });

    it('неуехавшая оценка не даёт карточке вернуться в новый сеанс', () => {
        // Сеанс собирается по серверу, а он последних оценок ещё не получил: без разбора
        // очереди закрытая карточка приходит снова.
        const deck = ['w1', 'w2'].map(entry);
        const server = new Map([['w1', state(2, NOW - DAY)]]);
        const queue = [answer('w1', 'know'), answer('w1', 'know', NOW + 20_000)];

        const stale = dueCards(deck, server, NOW + 30_000);
        const actual = dueCards(deck, replay(server, queue, rules), NOW + 30_000);

        expect(stale.map((card) => card.id)).toEqual(['w1', 'w2']);
        expect(actual.map((card) => card.id)).toEqual(['w2']);
    });

    it('оценка новой карточки заводит ей состояние', () => {
        const card = replay(new Map(), [answer('w1', 'know')], rules).get('w1');

        expect(card).toEqual(state(0, NOW, 1));
    });

    it('промах роняет карточку в изучение и помнит, откуда она упала', () => {
        const server = new Map([['w1', state(4, NOW + 16 * DAY)]]);

        const card = replay(server, [answer('w1', 'forgot')], rules).get('w1');

        expect(card).toEqual(state(0, NOW, 0, 1, 4));
    });

    it('карточка без своих оценок остаётся серверной', () => {
        const server = new Map([
            ['w1', state(3, NOW + DAY)],
            ['w2', state(5, NOW + 35 * DAY)],
        ]);

        expect(replay(server, [answer('w1', 'forgot')], rules).get('w2')).toEqual(server.get('w2'));
    });

    it('оценка с нечитаемым временем пропускается, а не портит срок', () => {
        // Битая запись в браузере: `NaN` в сроке спрятал бы карточку из расписания навсегда.
        const server = new Map([['w1', state(3, NOW + DAY)]]);
        const broken = { card_id: 'w1', verdict: 'know', answered_at: 'вчера' } as IAnswer;

        expect(replay(server, [broken], rules).get('w1')).toEqual(server.get('w1'));
    });

    it('исходную карту не меняет', () => {
        const server = new Map([['w1', state(2, NOW - DAY)]]);

        replay(server, [answer('w1', 'forgot')], rules);

        expect(server.get('w1')).toEqual(state(2, NOW - DAY));
    });
});

describe('когда очередь уезжает', () => {
    it('пустая очередь не уезжает даже после долгой тишины', () => {
        expect(isTimeToSend(0, BATCH, IDLE_PAUSE * 10)).toBe(false);
    });

    it('пока человек отвечает, запрос не уходит', () => {
        // Ручка считает запросы, а не оценки: запрос на нажатие съедал бы её предел за
        // четверть часа, и остаток сеанса не доехал бы вовсе.
        expect(isTimeToSend(1, BATCH, 0)).toBe(false);
        expect(isTimeToSend(50, BATCH, IDLE_PAUSE - 1)).toBe(false);
    });

    it('перестал отвечать — очередь уезжает', () => {
        expect(isTimeToSend(1, BATCH, IDLE_PAUSE)).toBe(true);
    });

    it('полная пачка уезжает, не дожидаясь тишины', () => {
        expect(isTimeToSend(BATCH, BATCH, 0)).toBe(true);
    });

    it('длинный сеанс укладывается в десяток запросов', () => {
        // Полтысячи нажатий подряд без единой паузы: пачки по сто, значит пять запросов.
        let pending = 0;
        let requests = 0;

        for (let press = 0; press < 500; press += 1) {
            pending += 1;

            if (!isTimeToSend(pending, BATCH, 0)) continue;

            requests += 1;
            pending = 0;
        }

        expect(requests).toBe(5);
    });
});

describe('пауза после отказа «слишком часто»', () => {
    it.each([
        ['30', 30_000],
        ['1', 1000],
    ])('ждёт столько, сколько просят: %s', (header, expected) => {
        expect(pauseFor(header)).toBe(expected);
    });

    it.each([[null], [''], ['потом'], ['0'], ['-5']])(
        'без внятной просьбы ждёт своё время: %s',
        (header) => {
            expect(pauseFor(header)).toBe(PAUSE_DEFAULT);
        },
    );

    it('дольше своего потолка не ждёт', () => {
        // Очередь должна уехать в этом же заходе, а не когда-нибудь.
        expect(pauseFor('86400')).toBe(PAUSE_LONGEST);
    });
});
