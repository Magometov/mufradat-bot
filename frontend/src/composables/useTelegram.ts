// #region Imports
// Types
import type { ITelegramThemeParams } from '../types/telegram';

// Vue
import { onUnmounted } from 'vue';
// #endregion

// Цвета клиента ложатся на наши переменные; чего клиент не дал, остаётся своим.
const THEME_MAP: Record<keyof ITelegramThemeParams, string> = {
    bg_color: '--base-0',
    secondary_bg_color: '--base-50',
    text_color: '--base-900',
    hint_color: '--base-500',
    button_color: '--primary-500',
    button_text_color: '--on-primary',
};

/**
 * Связь с клиентом Telegram. Вне Telegram приложение работает как обычная страница —
 * это единственный способ отлаживать его в браузере.
 */
export function useTelegram(): { init: () => void } {
    const webApp = window.Telegram?.WebApp ?? null;

    // Скрипт Telegram создаёт `WebApp` на любой странице, и вне клиента отдаёт
    // `colorScheme: 'light'`. Поэтому «внутри Telegram» определяется платформой: иначе
    // приложение в браузере встаёт в светлую тему вопреки системной.
    const client = webApp !== null && webApp.platform !== 'unknown' ? webApp : null;

    /**
     * Переносит тему клиента в CSS-переменные.
     */
    function applyTheme(): void {
        if (client === null) return;

        const root = document.documentElement;
        root.dataset.theme = client.colorScheme;

        Object.entries(THEME_MAP).forEach(([param, variable]) => {
            const color = client.themeParams[param as keyof ITelegramThemeParams];
            if (color) root.style.setProperty(variable, color);
        });
    }

    /**
     * Разворачивает окно на всю высоту и подхватывает тему.
     */
    function init(): void {
        if (client === null) return;

        client.ready();
        client.expand();
        applyTheme();
        client.onEvent('themeChanged', applyTheme);
    }

    onUnmounted(() => client?.offEvent('themeChanged', applyTheme));

    return { init };
}
