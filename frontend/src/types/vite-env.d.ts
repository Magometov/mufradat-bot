interface ImportMetaEnv {
    /** Пусто в обычной жизни: API живёт на том же адресе, что приложение. */
    readonly VITE_API_URL?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
