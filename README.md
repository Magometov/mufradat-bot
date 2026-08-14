# Mufradat Bot

Телеграм-бот и Mini App для запоминания арабских слов.

## Стек

Python 3.12, Django 6.0 + DRF, aiogram 3, Postgres 16, Vue 3 + Vite, Caddy, Docker Compose.

## Структура

```
backend/               Django: колода, админка, API
    apps/vocabulary/   модели Word + WordForm и Phrase, админка
    apps/common/       общее для всего: журнал входов, сверка подписи Telegram
    apps/api/          DRF: GET /api/v1/cards/ — вся колода одним ответом
    config/            настройки, urls, wsgi
bot/                   aiogram: приветствие и заглушка. Django не использует
frontend/              Vue 3: начальный экран и прогон по карточкам
flags/                 признак техработ, его ставит make maintenance-on
docs/                  дизайн и планы
Caddyfile              один сайт: статика файлами, /api и /admin в Django
docker-compose.yml     разработка: в контейнере только база
docker-compose.prod.yml  сервер: db, backend, bot, caddy
```

Колоду наполняют админка и бот. К базе бот не обращается: он пишет через служебные
ручки бэкенда, закрытые общим секретом. Переменные окружения — в `.env.example`.

## Техработы

```
make maintenance-on     сайт отдаёт страницу о работах, бот — сообщение
make maintenance-off
```

Признак — файл `flags/maintenance`. Caddy проверяет его на каждом запросе, бот на
каждом сообщении, поэтому переключение мгновенное. Админка при работах остаётся
открытой.
