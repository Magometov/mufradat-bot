/** Только то, чем пользуется приложение. */
export interface ITelegramWebApp {
    ready: () => void;
    expand: () => void;
    /** Вне клиента Telegram приходит `unknown` — по этому и отличаем. */
    platform: string;
    /** Подписанные Telegram данные о том, кто открыл приложение. В браузере — пусто. */
    initData: string;
}

declare global {
    interface Window {
        Telegram?: { WebApp: ITelegramWebApp };
    }
}
