<script setup lang="ts">
    // #region Imports
    // Types
    import type { TVerdict } from '../../types/progress';
    import type { ICardSide, IRunCard } from '../../types/run';

    // Vue
    import { computed } from 'vue';
    // #endregion

    // #region Props
    const props = withDefaults(
        defineProps<{
            card: IRunCard;
            isFlipped: boolean;
            /** Что засчитается, если отпустить сейчас. Пусто — метки нет. */
            mark?: TVerdict | '';
        }>(),
        { mark: '' },
    );
    // #endregion

    // #region Data
    const MARK_TEXT: Record<TVerdict, string> = {
        know: 'Помню',
        forgot: 'Не помню',
    };

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
        <div :class="$style.RunCard__mover" data-mover>
            <div
                :class="[
                    $style.RunCard__inner,
                    props.isFlipped && $style['RunCard__inner--flipped'],
                ]"
            >
                <!-- Лицо без модификатора: повёрнут оборот, а лицо лежит как есть. -->
                <div :class="$style.RunCard__face">
                    <p
                        :class="
                            front.isArabic ? $style.RunCard__arabic : $style.RunCard__translation
                        "
                        :dir="front.isArabic ? 'rtl' : undefined"
                        :lang="front.isArabic ? 'ar' : undefined"
                    >
                        {{ front.text }}
                    </p>
                </div>

                <div :class="[$style.RunCard__face, $style['RunCard__face--back']]">
                    <p
                        :class="
                            back.isArabic ? $style.RunCard__arabic : $style.RunCard__translation
                        "
                        :dir="back.isArabic ? 'rtl' : undefined"
                        :lang="back.isArabic ? 'ar' : undefined"
                    >
                        {{ back.text }}
                    </p>

                    <span :class="$style.RunCard__rule"></span>

                    <!-- Картинка только на обороте: на лице она подменила бы припоминание
                         узнаванием картинки. Загрузка не отложенная: оборот скрыт, и
                         браузер тянул бы файл в момент переворота — отсюда провал на
                         первом. Заранее их просит предзагрузка прогона. -->
                    <img
                        v-if="props.card.entry.image"
                        :class="$style.RunCard__image"
                        :src="props.card.entry.image"
                        :alt="props.card.entry.translation_ru"
                        decoding="async"
                        loading="eager"
                        :width="props.card.entry.image_width ?? undefined"
                        :height="props.card.entry.image_height ?? undefined"
                    />

                    <p v-if="props.card.entry.transliteration" :class="$style.RunCard__translit">
                        {{ props.card.entry.transliteration }}
                    </p>
                </div>
            </div>

            <!-- Метка идёт после сторон: у перевёрнутого слоя своя трёхмерная сцена, и
                 внутри неё порядок наложения решает не z-index, а он сам. -->
            <span
                v-if="props.mark"
                :class="[$style.RunCard__mark, $style[`RunCard__mark--${props.mark}`]]"
                aria-hidden="true"
            >
                {{ MARK_TEXT[props.mark] }}
            </span>
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

        // Метка лежит на утягиваемом слое, поэтому едет вместе с карточкой.
        &__mark {
            position: absolute;
            top: 1.6rem;
            left: 1.6rem;
            z-index: 1;
            padding: 0.4rem 1.2rem;
            border-radius: 1rem;
            font-size: 1.4rem;
            font-weight: 700;
        }

        &__mark--know {
            background: var(--good-soft);
            color: var(--good);
        }

        &__mark--forgot {
            background: var(--bad-soft);
            color: var(--bad);
        }

        // Двигается при свайпе только этот слой: карточки под ним стоят на месте, и
        // видно, что колода не кончилась.
        &__mover {
            position: absolute;
            top: 0;
            right: 0;
            bottom: 1.6rem;
            left: 0;
            transition: transform 0.22s ease-out;
            // `will-change` здесь нельзя: он создаёт и уничтожает слой отрисовки на каждый
            // жест, и в этот момент скругление успевает мигнуть прямоугольником. Слой и так
            // поднимается от `translate3d`, пока палец ведёт.
        }

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
            gap: 2rem;
            padding: 2.6rem;
            overflow-y: auto;
            border-radius: 2.4rem;
            background: var(--surface);
            backface-visibility: hidden;
            text-align: center;
            // Обе стороны с трансформацией с самого начала: иначе слои отрисовки под них
            // создаются в момент первого переворота, и он идёт с провалом.
            transform: translateZ(0);

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
        .RunCard__inner,
        .RunCard__mover {
            transition: none;
        }
    }
</style>
