/**
 * Форма слова по числу. Формы передаются тройкой: для одного, для двух-четырёх и для остальных.
 */
export function plural(count: number, forms: [string, string, string]): string {
    const tail = Math.abs(count) % 100;
    const last = tail % 10;

    if (tail > 10 && tail < 20) return forms[2];
    if (last === 1) return forms[0];
    if (last > 1 && last < 5) return forms[1];

    return forms[2];
}

/**
 * «День» в нужном числе.
 */
export function dayWord(count: number): string {
    return plural(count, ['день', 'дня', 'дней']);
}

/**
 * «Слово» в нужном числе.
 */
export function wordWord(count: number): string {
    return plural(count, ['слово', 'слова', 'слов']);
}

/**
 * «Карточка» в нужном числе.
 */
export function cardWord(count: number): string {
    return plural(count, ['карточка', 'карточки', 'карточек']);
}

/**
 * «Раз» в нужном числе.
 */
export function timeWord(count: number): string {
    return plural(count, ['раз', 'раза', 'раз']);
}

/**
 * «Раздел» в родительном падеже: слово всегда идёт после «из».
 */
export function sectionWord(count: number): string {
    return plural(count, ['раздела', 'разделов', 'разделов']);
}
