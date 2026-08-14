/**
 * Отмечает вход в приложение. Что это за человек, бэкенд разберёт сам: в `initData`
 * лежит подпись Telegram, а из браузера строка приходит пустой — это и значит «с сайта».
 */
export async function logVisit(url: string, initData: string): Promise<void> {
    try {
        await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ init_data: initData }),
        });
    } catch {
        // Незаписанный вход — не повод мешать колоде.
    }
}
