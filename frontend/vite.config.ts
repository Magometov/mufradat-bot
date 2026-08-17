import vue from '@vitejs/plugin-vue';
// `defineConfig` из vitest: он тот же, что у vite, только знает про блок `test`.
import { defineConfig } from 'vitest/config';

// Django с хоста. Прокси нужен, чтобы приложение звало API своим же адресом: тогда
// нет ни CORS, ни разъезда схемы http/https при работе через туннель.
const BACKEND = 'http://127.0.0.1:8000';

export default defineConfig({
    plugins: [vue()],
    // Тестами закрыты только чистые функции: сборка сеанса и разбор жеста. Экраны
    // проверяются глазами — быстрее и честнее любого теста на разметку.
    test: { include: ['src/**/*.spec.ts'] },
    server: {
        host: true,
        // Адрес туннеля меняется при каждом запуске, перечислять его негде.
        allowedHosts: true,
        // `changeOrigin: false` обязателен: Django собирает адрес картинки из заголовка
        // `Host`, и он должен остаться адресом приложения. Короткая запись
        // (`'/api': BACKEND`) подменяет `Host` на адрес цели, и тогда с телефона
        // картинка ведёт на сам телефон — `127.0.0.1:8000`.
        proxy: {
            '/api': { target: BACKEND, changeOrigin: false },
            '/m': { target: BACKEND, changeOrigin: false },
        },
    },
});
