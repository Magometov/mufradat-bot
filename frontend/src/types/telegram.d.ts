/** Цвета темы клиента; любое поле может отсутствовать. */
export interface ITelegramThemeParams {
    bg_color?: string;
    secondary_bg_color?: string;
    text_color?: string;
    hint_color?: string;
    button_color?: string;
    button_text_color?: string;
}

/** Только то, чем пользуется приложение. */
export interface ITelegramWebApp {
    ready: () => void;
    expand: () => void;
    /** Вне клиента Telegram приходит `unknown` — по этому и отличаем. */
    platform: string;
    colorScheme: 'light' | 'dark';
    themeParams: ITelegramThemeParams;
    onEvent: (event: 'themeChanged', handler: () => void) => void;
    offEvent: (event: 'themeChanged', handler: () => void) => void;
}

declare global {
    interface Window {
        Telegram?: { WebApp: ITelegramWebApp };
    }
}
