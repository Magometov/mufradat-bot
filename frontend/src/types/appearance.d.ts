import type { Ref } from 'vue';

/** Оформление приложения. Разделы колоды — это `ITheme`, понятие другое. */
export type TAppearance = 'light' | 'dark';

export interface IUseAppearance {
    appearance: Ref<TAppearance>;
    toggle: () => void;
}
