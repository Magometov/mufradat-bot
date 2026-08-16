/**
 * Связь с клиентом Telegram. Вне Telegram приложение работает как обычная страница —
 * это единственный способ отлаживать его в браузере.
 *
 * Оформление у клиента не спрашивают: приложение выглядит одинаково везде, а светлое
 * или тёмное выбирает сам человек кнопкой на первом экране.
 */
export function useTelegram(): { initData: string; init: () => void } {
    const webApp = window.Telegram?.WebApp ?? null;

    // Скрипт Telegram создаёт `WebApp` на любой странице, поэтому «внутри клиента»
    // определяется платформой: вне его она приходит как `unknown`.
    const client = webApp !== null && webApp.platform !== 'unknown' ? webApp : null;

    /**
     * Разворачивает окно на всю высоту.
     */
    function init(): void {
        if (client === null) return;

        client.ready();
        client.expand();
    }

    // Берётся у `webApp`, а не у `client`: вне Telegram строка и так пустая, а сверять
    // платформу тут нечего — подпись проверит бэкенд.
    return { initData: webApp?.initData ?? '', init };
}
