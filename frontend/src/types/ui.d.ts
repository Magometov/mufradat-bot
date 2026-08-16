export type TButtonVariant = 'primary' | 'accent' | 'soft' | 'ghost';

/** Размер кнопки: `large` — для главного действия экрана. */
export type TButtonSize = 'default' | 'large';

export interface IUiButtonProps {
    variant?: TButtonVariant;
    isDisabled?: boolean;
    size?: TButtonSize;
}
