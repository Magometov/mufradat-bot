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
</script>

<template>
    <!-- Жесты разбирает сцена прогона, поэтому своего обработчика здесь нет. Роль и
         tabindex — не для мыши: без них карточка не доступна ни с клавиатуры, ни
         скринридеру, для которого это была бы просто пара абзацев. -->
    <div :class="$style.RunCard" role="button" tabindex="0" :aria-label="hint">
        <!-- Карточки под верхней выглядывают по краям: видно, что колода не кончилась. -->
        <div
            :class="[$style.RunCard__behind, $style['RunCard__behind--far']]"
            aria-hidden="true"
        ></div>
        <div
            :class="[$style.RunCard__behind, $style['RunCard__behind--near']]"
            aria-hidden="true"
        ></div>

        <div :class="[$style.RunCard__inner, props.isFlipped && $style['RunCard__inner--flipped']]">
            <!-- Лицо без модификатора: повёрнут оборот, а лицо лежит как есть. -->
            <div :class="$style.RunCard__face">
                <p
                    :class="front.isArabic ? $style.RunCard__arabic : $style.RunCard__translation"
                    :dir="front.isArabic ? 'rtl' : undefined"
                    :lang="front.isArabic ? 'ar' : undefined"
                >
                    {{ front.text }}
                </p>
            </div>

            <div :class="[$style.RunCard__face, $style['RunCard__face--back']]">
                <p
                    :class="back.isArabic ? $style.RunCard__arabic : $style.RunCard__translation"
                    :dir="back.isArabic ? 'rtl' : undefined"
                    :lang="back.isArabic ? 'ar' : undefined"
                >
                    {{ back.text }}
                </p>

                <span :class="$style.RunCard__rule"></span>

                <!-- Картинка только на обороте: на лице она подменила бы припоминание
                     узнаванием картинки. -->
                <img
                    v-if="props.card.entry.image"
                    :class="$style.RunCard__image"
                    :src="props.card.entry.image"
                    :alt="props.card.entry.translation_ru"
                    decoding="async"
                    loading="lazy"
                    :width="props.card.entry.image_width ?? undefined"
                    :height="props.card.entry.image_height ?? undefined"
                />

                <p v-if="props.card.entry.transliteration" :class="$style.RunCard__translit">
                    {{ props.card.entry.transliteration }}
                </p>
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
        cursor: pointer;
        user-select: none;

        // Обводка только для пришедшего с клавиатуры: карточку нажимают пальцем, и
        // рамка после каждого касания была бы шумом.
        &:focus-visible {
            outline: 2px solid var(--accent);
            outline-offset: 2px;
            border-radius: 2.4rem;
        }

        // Тон, а не прозрачность: полупрозрачная белая карточка на светлом фоне в него
        // же и утекает, а разница тонов держится при любой теме.
        &__behind {
            position: absolute;
            border-radius: 2.4rem;
            background: var(--behind);
            box-shadow: 0 0.6rem 1.6rem -0.8rem var(--under);
        }

        &__behind--far {
            top: 1.6rem;
            right: 2.6rem;
            bottom: 0;
            left: 2.6rem;
        }

        &__behind--near {
            top: 0.8rem;
            right: 1.4rem;
            bottom: 0.8rem;
            left: 1.4rem;
        }

        &__inner {
            position: absolute;
            top: 0;
            right: 0;
            bottom: 1.6rem;
            left: 0;
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
            gap: 2rem;
            padding: 2.6rem;
            overflow-y: auto;
            border-radius: 2.4rem;
            background: var(--surface);
            box-shadow: var(--lift);
            backface-visibility: hidden;
            text-align: center;

            &--back {
                transform: rotateY(180deg);
            }
        }

        &__arabic {
            font-family: var(--font-arabic);
            font-size: 5.2rem;
            line-height: 1.7;
            word-break: break-word;
        }

        &__translation {
            font-size: 2.8rem;
            font-weight: 500;
            word-break: break-word;
        }

        // Короткая черта под ответом: отделяет слово от картинки, не рисуя рамок.
        &__rule {
            width: 4.6rem;
            height: 2px;
            border-radius: 2px;
            background: var(--accent);
            opacity: 0.45;
        }

        // Рамки нет: карточка и так светлее фона, обводка на ней ничего не отделяет.
        // Только максимальные ограничения — растянуть маленький файл значит сделать
        // мыло заметнее, резкости от этого не появится.
        &__image {
            width: auto;
            height: auto;
            max-width: 100%;
            max-height: 22rem;
            border-radius: 1.4rem;
            object-fit: contain;
        }

        &__translit {
            color: var(--muted);
            font-size: 1.6rem;
        }
    }

    // Переворот — единственное движение карточки; тому, кто просил его убрать, стороны
    // меняются сразу.
    @media (prefers-reduced-motion: reduce) {
        .RunCard__inner {
            transition: none;
        }
    }
</style>
