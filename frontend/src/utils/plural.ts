/**
 * Русская форма слова по числу: 1 слово, 2 слова, 5 слов, 11 слов, 21 слово.
 *
 * Формы передаются тройкой: для одного, для двух-четырёх, для остального.
 */
export function plural(count: number, forms: [string, string, string]): string {
    const tens = Math.abs(count) % 100;
    const ones = Math.abs(count) % 10;

    // Второй десяток — исключение целиком: 11 слов, 14 слов.
    if (tens > 10 && tens < 20) return forms[2];
    if (ones === 1) return forms[0];
    if (ones >= 2 && ones <= 4) return forms[1];

    return forms[2];
}
