/** Карточка, как её отдаёт `GET /api/v1/cards/`. */
export interface IEntry {
    /** Формы слов и фразы лежат в разных таблицах, буква разводит их номера: `w12`, `p7`. */
    id: string;
    arabic: string;
    translation_ru: string;
    /** Приходит пустой строкой, а не `null`, когда транслитерации нет. */
    transliteration: string;
    /** Снятая галочка — фраза; в прогон по словам такая карточка не идёт. */
    is_word: boolean;
    /** Полный URL или `null`. */
    image: string | null;
    /** Размеры файла. Пустые без картинки и у карточек, снятых до появления полей. */
    image_width: number | null;
    image_height: number | null;
    /** Коды тем карточки. Фильтр по теме считает приложение, поэтому они едут с колодой. */
    themes: string[];
}
