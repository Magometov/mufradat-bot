export type TButtonVariant = 'primary' | 'accent' | 'soft' | 'ghost';

export interface IUiButtonProps {
    variant?: TButtonVariant;
    isDisabled?: boolean;
}
