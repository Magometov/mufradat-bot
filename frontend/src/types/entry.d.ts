/** Карточка, как её отдаёт `GET /api/v1/entries/`. */
export interface IEntry {
    id: number;
    arabic: string;
    translation_ru: string;
    /** Приходит пустой строкой, а не `null`, когда транслитерации нет. */
    transliteration: string;
    /** Снятая галочка — фраза; в прогон по словам такая карточка не идёт. */
    is_word: boolean;
    /** Полный URL или `null`. */
    image: string | null;
    /** Коды тем карточки. Фильтр по теме считает приложение, поэтому они едут с колодой. */
    themes: string[];
}
