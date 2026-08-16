import js from '@eslint/js';
import prettier from '@vue/eslint-config-prettier';
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript';
import vue from 'eslint-plugin-vue';
import globals from 'globals';

export default defineConfigWithVueTs(
    { ignores: ['dist/**', 'node_modules/**'] },
    js.configs.recommended,
    vue.configs['flat/recommended'],
    vueTsConfigs.recommended,
    // Форматирование — дело Prettier; правила, которые с ним спорят, здесь выключаются.
    prettier,
    {
        files: ['**/*.{ts,vue}'],
        languageOptions: {
            globals: globals.browser,
        },
        rules: {
            // Правила проекта: any запрещён, строгое сравнение обязательно.
            '@typescript-eslint/no-explicit-any': 'error',
            eqeqeq: ['error', 'always'],
            // Имя компонента из одного слова — это про страницы и лейауты, которых тут
            // нет: все свои компоненты и так названы в два слова.
            'vue/multi-word-component-names': 'error',
            // Порядок частей SFC зафиксирован: логика, разметка, стили.
            'vue/block-order': ['error', { order: ['script', 'template', 'style'] }],
        },
    },
);
