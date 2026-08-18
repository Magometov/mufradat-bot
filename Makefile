# Команды сервера. Все цели работают с прод-стеком; `make` без аргументов покажет
# список. Compose-файл зафиксирован, а не выбирается переменной: на сервере эти
# команды набираются десятками раз, и перепутать файл дороже, чем не иметь выбора.
COMPOSE := docker compose -f docker-compose.prod.yml

# `backend` и `bot` собираются из одного образа. Пересобрать один — оставить второй
# на старом коде, поэтому они всегда идут парой.
APP := backend bot

# Аргументы целей: `make logs S=bot N=100`, `make backup OUT=db.sql`.
S ?=
N ?= 50
OUT ?= backup-$(shell date +%F-%H%M).sql

.DEFAULT_GOAL := help

.PHONY: help
help: ## Показать этот список
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?##' $(MAKEFILE_LIST) \
		| awk -F':.*?## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# --- Разработка: тесты ----------------------------------------------------------

.PHONY: test
test: test-back test-front ## Прогнать все тесты

.PHONY: test-back
test-back: ## Тесты бэкенда. База должна быть поднята: docker compose up -d db
	uv run --group backend --group bot --group dev pytest

.PHONY: test-front
test-front: ## Тесты фронтенда: чистые функции сеанса
	cd frontend && npm run test

# --- Сервер: сборка и запуск ---------------------------------------------------

.PHONY: build
build: ## Пересобрать и поднять все контейнеры
	$(COMPOSE) up -d --build

.PHONY: back
back: ## Пересобрать только бэкенд — backend и bot вместе
	$(COMPOSE) up -d --build $(APP)

.PHONY: front
front: ## Пересобрать только фронтенд
	$(COMPOSE) up -d --build caddy

.PHONY: rebuild
rebuild: ## Полная пересборка без кэша — долго, ест память
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d --force-recreate

.PHONY: up
up: ## Поднять стек, ничего не пересобирая
	$(COMPOSE) up -d

.PHONY: down
down: ## Остановить стек. Данные в томах остаются
	$(COMPOSE) down

.PHONY: restart
restart: ## Перезапустить сервис: make restart S=bot
	$(COMPOSE) restart $(S)

# --- Сервер: заглушка на время работ ---------------------------------------------

# Признак — файл, который Caddy и бот проверяют на каждом обращении. Поэтому включение
# и снятие мгновенные и не требуют ни правки .env, ни пересоздания контейнеров.
.PHONY: maintenance-on
maintenance-on: ## Включить заглушку «Технические работы» в боте и на сайте
	@mkdir -p flags && touch flags/maintenance
	@echo "Заглушка включена."

.PHONY: maintenance-off
maintenance-off: ## Снять заглушку
	@rm -f flags/maintenance
	@echo "Заглушка снята."

# --- Сервер: Django ------------------------------------------------------------

.PHONY: migrate
migrate: ## Применить миграции в контейнере
	$(COMPOSE) exec backend python manage.py migrate

.PHONY: superuser
superuser: ## Создать суперпользователя админки
	$(COMPOSE) exec backend python manage.py createsuperuser

.PHONY: shell
shell: ## Django shell в контейнере
	$(COMPOSE) exec backend python manage.py shell

.PHONY: pictures
pictures: ## Перенести картинки колоды в бакет и собрать карточки для чата
	$(COMPOSE) exec backend python manage.py sync_pictures

.PHONY: word
word: ## Отправить слово в группу сейчас, не дожидаясь часа
	$(COMPOSE) exec bot python -m bot.group

.PHONY: deploy
deploy: ## Забрать код, пересобрать, применить миграции
	git pull
	$(COMPOSE) up -d --build
	$(COMPOSE) exec backend python manage.py migrate

# --- Сервер: база --------------------------------------------------------------

# Пароль и имя базы берутся из окружения самого контейнера, поэтому в команде их нет.
# Имя файла по умолчанию с датой: перезаписать вчерашний дамп сегодняшним — потерять
# единственную точку возврата.
.PHONY: backup
backup: ## Дамп базы в файл: make backup [OUT=db.sql]
	@$(COMPOSE) exec -T db sh -c 'pg_dump -U $$POSTGRES_USER $$POSTGRES_DB' > $(OUT)
	@ls -lh $(OUT)

# --- Сервер: наблюдение --------------------------------------------------------

.PHONY: ps
ps: ## Что запущено
	$(COMPOSE) ps

.PHONY: logs
logs: ## Логи: make logs [S=bot] [N=100]
	$(COMPOSE) logs --tail=$(N) $(S)

.PHONY: tail
tail: ## Логи потоком: make tail [S=backend] [N=100]
	$(COMPOSE) logs -f --tail=$(N) $(S)

# --- Сервер: место на диске ----------------------------------------------------
#
# Тома не удаляет ни одна цель ниже, даже `clean-hard`: в `pgdata` лежит база,
# а `docker volume prune` при остановленном стеке снёс бы её без вопросов.

.PHONY: disk
disk: ## Сколько занято: диск и docker отдельно
	@df -h / | tail -1
	@echo
	@docker system df

.PHONY: clean
clean: ## Освободить место: висячие образы, мёртвые контейнеры, кэш сборки
	docker container prune -f
	docker image prune -f
	docker builder prune -af
	@echo
	@$(MAKE) --no-print-directory disk

.PHONY: clean-hard
clean-hard: ## Ещё и все неиспользуемые образы с системными логами. Стек держать поднятым
	docker container prune -f
	docker image prune -af
	docker builder prune -af
	sudo journalctl --vacuum-size=100M
	sudo apt-get clean
	@echo
	@$(MAKE) --no-print-directory disk
