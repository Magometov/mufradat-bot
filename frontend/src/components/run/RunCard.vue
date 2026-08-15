<script setup lang="ts">
    // #region Imports
    // Types
    import type { ICardSide, IRunCard } from '../../types/run';

    // Vue
    import { computed } from 'vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            card: IRunCard;
            isFlipped: boolean;
        }>(),
        {},
    );
    // #endregion

    // #region Emits
    const emit = defineEmits<{
        flip: [];
    }>();
    // #endregion

    // #region Data
    const HINT = {
        forward: 'нажми, чтобы увидеть перевод',
        reversed: 'нажми, чтобы увидеть арабское',
    } as const;
    // #endregion

    // #region Computed
    // Лицо и оборот меняются местами, а не переписываются: правило одно на оба
    // направления — на лице вопрос, на обороте ответ.
    const front = computed<ICardSide>(() =>
        props.card.isReversed
            ? { text: props.card.entry.translation_ru, isArabic: false }
            : { text: props.card.entry.arabic, isArabic: true },
    );

    const back = computed<ICardSide>(() =>
        props.card.isReversed
            ? { text: props.card.entry.arabic, isArabic: true }
            : { text: props.card.entry.translation_ru, isArabic: false },
    );

    const hint = computed<string>(() => (props.card.isReversed ? HINT.reversed : HINT.forward));
    // #endregion

    // #region Methods
    /**
     * Переворачивает карточку: нажатие приходит с любого места лица и оборота.
     */
    function handleFlip(): void {
        emit('flip');
    }
    // #endregion
</script>

<template>
    <div :class="$style.RunCard" @click="handleFlip">
        <div
            :class="[$style.RunCard__inner, props.isFlipped && $style['RunCard__inner--flipped']]"
        >
            <!-- Лицо без модификатора: повёрнут оборот, а лицо лежит как есть. -->
            <div :class="$style.RunCard__face">
                <p
                    :class="front.isArabic ? $style.RunCard__arabic : $style.RunCard__translation"
                    :dir="front.isArabic ? 'rtl' : undefined"
                    :lang="front.isArabic ? 'ar' : undefined"
                >
                    {{ front.text }}
                </p>
                <p :class="$style.RunCard__hint">{{ hint }}</p>
            </div>

            <div :class="[$style.RunCard__face, $style['RunCard__face--back']]">
                <p
                    :class="back.isArabic ? $style.RunCard__arabic : $style.RunCard__translation"
                    :dir="back.isArabic ? 'rtl' : undefined"
                    :lang="back.isArabic ? 'ar' : undefined"
                >
                    {{ back.text }}
                </p>

                <p v-if="props.card.entry.transliteration" :class="$style.RunCard__translit">
                    {{ props.card.entry.transliteration }}
                </p>

                <!-- Картинка только на обороте: на лице она подменила бы припоминание
                     узнаванием картинки. -->
                <div v-if="props.card.entry.image" :class="$style.RunCard__frame">
                    <img
                        :class="$style.RunCard__image"
                        :src="props.card.entry.image"
                        :alt="props.card.entry.translation_ru"
                        decoding="async"
                        loading="lazy"
                        width="400"
                        height="260"
                        referrerpolicy="no-referrer"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<style module lang="scss">
    .RunCard {
        // Карточки при перелистывании накладываются друг на друга, поэтому место в
        // разметке держит контейнер, а не сама карточка.
        position: absolute;
        inset: 0;
        // Переворот трёхмерный: обе стороны лежат друг на друге.
        perspective: 100rem;
        user-select: none;

        &__inner {
            position: absolute;
            inset: 0;
            transform-style: preserve-3d;
            transition: transform 0.45s ease;

            &--flipped {
                transform: rotateY(180deg);
            }
        }

        &__face {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.6rem;
            padding: 2.4rem;
            overflow-y: auto;
            border: 1px solid var(--base-200);
            border-radius: 2rem;
            background: var(--base-50);
            backface-visibility: hidden;
            text-align: center;

            &--back {
                transform: rotateY(180deg);
            }
        }

        &__arabic {
            font-family: var(--font-arabic);
            font-size: 4.8rem;
            line-height: 1.8;
            word-break: break-word;
        }

        &__hint {
            color: var(--base-500);
            font-size: 1.4rem;
        }

        &__translation {
            font-size: 2.8rem;
            word-break: break-word;
        }

        &__translit {
            color: var(--base-500);
            font-size: 1.8rem;
        }

        // Рамка обнимает фото по его размеру: тогда маленький файл выглядит вставленным
        // нарочно, а не потерянным в пустом поле.
        &__frame {
            display: flex;
            max-width: 100%;
            padding: 0.8rem;
            border: 1px solid var(--base-200);
            border-radius: 1.6rem;
            background: var(--base-0);
        }

        // Только максимальные ограничения: растянуть маленький файл — значит сделать
        // мыло заметнее, резкости от этого не появится.
        &__image {
            display: block;
            width: auto;
            height: auto;
            max-width: 100%;
            max-height: 26rem;
            border-radius: 0.8rem;
            object-fit: contain;
            background: var(--base-50);
        }
    }
</style>
