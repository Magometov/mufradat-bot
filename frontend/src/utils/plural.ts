/**
 * Слово «день» в нужном числе: 1 день, 3 дня, 7 дней.
 */
export function dayWord(count: number): string {
    const tail = Math.abs(count) % 100;
    const last = tail % 10;

    if (tail > 10 && tail < 20) return 'дней';
    if (last === 1) return 'день';
    if (last > 1 && last < 5) return 'дня';

    return 'дней';
}
