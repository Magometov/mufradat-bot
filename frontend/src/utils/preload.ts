// Адреса, которые уже просили: браузер и сам не пойдёт за картинкой второй раз, но
// новый Image на каждый шаг прогона создаёт объекты на ровном месте.
const asked = new Set<string>();

/**
 * Просит браузер забрать картинки заранее. Пустые адреса пропускаются.
 */
export function preload(urls: (string | null)[]): void {
    urls.forEach((url) => {
        if (url === null || asked.has(url)) return;

        asked.add(url);
        new Image().src = url;
    });
}
