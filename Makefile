# Команды сервера и локальной разработки. `make` без аргументов покажет список.
#
# Compose-файл зафиксирован, а не выбирается переменной: на сервере эти команды
# набираются десятками раз, и перепутать описание дороже, чем не иметь выбора.
# Локальные цели ниже собраны отдельно и прод-стек не трогают.
COMPOSE := docker compose -f docker-compose.prod.yml

# `backend` и `bot` собираются из одного образа `mufradat-backend`. Пересобрать
# один — оставить второй на старом коде, поэтому они всегда идут парой.
PYTHON := backend bot

# Аргументы целей: `make logs S=bot N=100`, `make images LIMIT=10 ARGS=--replace`.
# Флаги команде передаются через `ARGS`, а не напрямую: `make images --replace`
# отдал бы `--replace` самому make. У `LIMIT` значения по умолчанию нет намеренно:
# пустая переменная означает «рисовать всё», а число молча урезало бы прогон.
S ?=
N ?= 50
LIMIT ?=
ARGS ?=

.DEFAULT_GOAL := help

.PHONY: help
help: ## Показать этот список
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?##' $(MAKEFILE_LIST) \
		| awk -F':.*?## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# --- Сервер: сборка и запуск ---------------------------------------------------

.PHONY: build
build: ## Пересобрать и поднять все контейнеры
	$(COMPOSE) up -d --build

.PHONY: back
back: ## Пересобрать только бэкенд — backend и bot вместе
	$(COMPOSE) up -d --build $(PYTHON)

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

# --- Сервер: Django ------------------------------------------------------------

.PHONY: migrate
migrate: ## Применить миграции в контейнере
	$(COMPOSE) exec backend python manage.py migrate

.PHONY: themes
themes: ## Расставить темы карточек по правилам
	$(COMPOSE) exec backend python manage.py assign_themes

.PHONY: words
words: ## Отметить отдельные слова: make words [ARGS=--dry-run]
	$(COMPOSE) exec backend python manage.py mark_words $(ARGS)

.PHONY: images
images: ## Картинки карточкам: make images [LIMIT=10] [ARGS=--replace]
	$(COMPOSE) exec backend python manage.py generate_images $(if $(LIMIT),--limit $(LIMIT),) $(ARGS)

.PHONY: superuser
superuser: ## Создать суперпользователя админки
	$(COMPOSE) exec backend python manage.py createsuperuser

.PHONY: shell
shell: ## Django shell в контейнере
	$(COMPOSE) exec backend python manage.py shell

.PHONY: deploy
deploy: ## Забрать код, пересобрать, применить миграции
	git pull
	$(COMPOSE) up -d --build
	$(COMPOSE) exec backend python manage.py migrate

# --- Сервер: наблюдение --------------------------------------------------------

.PHONY: ps
ps: ## Что запущено
	$(COMPOSE) ps

.PHONY: logs
logs: ## Логи: make logs [S=bot] [N=100]
	$(COMPOSE) logs --tail=$(N) $(S)

.PHONY: tail
tail: ## Логи потоком: make tail [S=backend]
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
