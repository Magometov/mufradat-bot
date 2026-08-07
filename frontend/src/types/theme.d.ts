/** Тема колоды, как её отдаёт `GET /api/v1/themes/`. Порядок в ответе — порядок кнопок. */
export interface ITheme {
    slug: string;
    name: string;
}
