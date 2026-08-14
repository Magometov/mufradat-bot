# Mufradat Bot

Телеграм-бот и Mini App для запоминания арабских слов.

## Стек

Python 3.12, Django 6.0 + DRF, aiogram 3, Postgres 16, Vue 3 + Vite, Caddy, Docker Compose.
Зависимости python — через `uv`.

## Структура

```
backend/
    apps/vocabulary/   единственная модель Entry и админка
    apps/bot/          aiogram: приветствие и разбор ввода
    apps/api/          DRF: GET /api/v1/entries/ — вся колода одним ответом
    config/            настройки, urls, wsgi
    tests/
frontend/              Vue 3: начальный экран и прогон по карточкам
docs/                  дизайн и планы
Caddyfile              один сайт: статика файлами, /api и /admin в Django
docker-compose.yml     разработка: в контейнере только база
docker-compose.prod.yml  сервер: db, backend, bot, caddy
```
