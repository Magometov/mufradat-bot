# Ввод в строй: Selectel + домен

> **Как проходить:** этапы строго по порядку, шаги — галочками. Каждый этап заканчивается
> проверкой; без зелёной проверки следующий не начинается. Команды выполняет владелец.

**Цель:** поднять бот, API, админку и Mini App на купленном VPS под своим доменом с https
и включить кнопку приложения в боте.

**Как устроено:** четыре контейнера из `docker-compose.prod.yml` (`db`, `backend`, `bot`,
`caddy`), сертификат Caddy получает сам, код едет на сервер из приватного репозитория
GitHub по ключу только на чтение. Разбор решений — §14 спеки.

**Что покупается:** Selectel, готовый тариф **VDS 2-4-50** (2 vCPU / 4 ГБ / 50 ГБ, IP и
3 ТБ трафика включены) — 650 ₽/мес. Домен `.ru` у reg.ru — ~199 ₽ за первый год.

## Общие ограничения

- Прод-команды **только** с `-f docker-compose.prod.yml`. Без флага поднимется
  разработочный вариант.
- `backend` и `bot` — один образ. Пересобирать **всегда оба**: `up -d --build backend bot`.
- Правка фронтенда = пересборка `caddy` (`up -d --build caddy`), своего сервиса у него нет.
- `DJANGO_DEBUG` на сервере прибит в compose, значение из `.env` не читается.
- Один токен — один поллер. Пока бот работает на сервере, локальный `runbot` с тем же
  токеном получит от Telegram 409.
- `.env` на сервере пишется руками, в git его нет и не будет — `git pull` его не затронет.
- Репозиторий приватный, ключ на сервере — только на чтение.
- Пуш в этот репозиторий разрешён владельцем 2026-08-06. Других удалённых адресов не
  добавлять.

---

## Этап 0: Покупки

- [ ] **Шаг 1: Создать сервер в Selectel**

Облачные серверы → готовый тариф **VDS 2-4-50**. Образ — **Ubuntu 24.04 LTS**. SSH-ключ
добавить на этом же экране, тогда пароль root не понадобится. Регион — Москва или СПб.

- [ ] **Шаг 2: Проверить, что порты не закрыты панелью**

В карточке сервера — раздел файрвола или групп безопасности. Нужны открытыми `22`, `80`,
`443`. Без 80-го Caddy не выпустит сертификат.

- [ ] **Шаг 3: Купить домен**

reg.ru, зона `.ru` — 199 ₽ регистрация, 399 ₽ продление. Имя короткое латиницей: его видно
в Telegram при открытии приложения. Для `.ru` регистратор запросит паспортные данные; если
не хочется — `.app` или `.site` без документов, но продление 1200–1500 ₽/год.

- [ ] **Шаг 4: Прописать A-запись**

В DNS у регистратора: тип `A`, имя `@`, значение — IP сервера, TTL 600. Поддомен `www` не
нужен: в `Caddyfile` один адрес из `DOMAIN`, `www` он обслуживать не будет.

**Проверка этапа:** на своей машине

```bash
dig +short ВАШ-ДОМЕН.ru
```

Ожидается IP сервера. Если пусто — ждать распространения (до часа) и повторить. Дальше не
идти: без DNS сертификат не выпустится.

---

## Этап 1: Сервер — учётная запись и Docker

- [ ] **Шаг 1: Зайти root'ом и обновить систему**

```bash
ssh root@IP-СЕРВЕРА
apt update && apt upgrade -y
```

- [ ] **Шаг 2: Создать рабочего пользователя и дать ему sudo без пароля**

```bash
adduser --disabled-password --gecos "" mufradat
usermod -aG sudo mufradat
rsync --archive --chown=mufradat:mufradat ~/.ssh /home/mufradat/
echo 'mufradat ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-mufradat
chmod 440 /etc/sudoers.d/90-mufradat
```

Пароля у пользователя нет намеренно: вход только по ключу. Но тогда и `sudo` спросить
пароль не сможет — отсюда `NOPASSWD`. Так же поступает cloud-init со своим пользователем
`ubuntu`. Цена честная: у кого есть ssh-ключ, у того есть root. Ключ — единственная дверь
на сервер, так что второго замка на ней всё равно нет.

- [ ] **Шаг 3: Прописать сервер в свой ssh-config**

На своей машине, в `~/.ssh/config`:

```
Host mufradat
    HostName IP-СЕРВЕРА
    User mufradat
```

- [ ] **Шаг 4: Проверить вход новым пользователем, не закрывая сессию root**

Из **второго** окна терминала:

```bash
ssh mufradat 'whoami && sudo whoami'
```

Ожидается `mufradat` и `root`. Пока это не сработало, сессию root не закрывать: следующий
шаг выключает вход root'ом, и при ошибке в ключах сервер останется без входа вообще.

- [ ] **Шаг 5: Закрыть вход по паролю и вход root'ом**

В сессии root:

```bash
printf 'PasswordAuthentication no\nPermitRootLogin no\n' > /etc/ssh/sshd_config.d/99-hardening.conf
systemctl reload ssh
sshd -T | grep -E "passwordauthentication|permitrootlogin"
```

Ожидается `passwordauthentication no` и `permitrootlogin no`. Отдельный файл в
`sshd_config.d/` нужен потому, что на Ubuntu 24.04 настройки из этого каталога перекрывают
правку самого `sshd_config`.

`fail2ban` не ставим: подбирать нечего, когда вход по паролю выключен.

- [ ] **Шаг 6: Проверить автообновления безопасности**

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
systemctl is-enabled unattended-upgrades
```

Ожидается по единице в обеих строках и `enabled`. На Ubuntu 24.04 это включено из коробки;
если нет — `apt install -y unattended-upgrades`. Сервер никто не сторожит, заплатки
безопасности должны ставиться сами.

- [ ] **Шаг 7: Добавить 2 ГБ подкачки**

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
free -h
```

Ожидается строка `Swap:` с 2,0Gi. Подкачка — страховка для сборки фронтенда: `npm ci` и
`vite build` на дешёвой линейке с общим ядром — самый жадный шаг за всё развёртывание.

- [ ] **Шаг 8: Поставить Docker из официального репозитория**

```bash
apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker mufradat
```

В репозитории Ubuntu (`docker.io` + `docker-compose-v2`) версии старее; нам нужны compose v2
и buildx как есть.

- [ ] **Шаг 9: Включить файрвол**

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443
ufw --force enable
ufw status
```

`ufw allow 443` открывает и tcp, и udp — udp нужен Caddy для HTTP/3. Помнить: порты,
опубликованные контейнерами, идут мимо ufw. Базу защищает то, что в прод-описании её порт
не публикуется, а не эти правила.

- [ ] **Шаг 10: Короткая команда для прод-стека (по желанию)**

Оболочка — обычный bash, ставить ничего не нужно. Решение владельца: никаких zsh и
надстроек. Единственное, что окупается, — две строки в `.bashrc`:

```bash
cat >> /home/mufradat/.bashrc <<'EOF'
bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'
alias dc='docker compose -f ~/mufradat/docker-compose.prod.yml --project-directory ~/mufradat'
EOF
```

Стрелка вверх листает только команды, начинавшиеся на набранное. `dc ps` вместо
`docker compose -f docker-compose.prod.yml ps` — эта длинная команда набирается десятки раз.

**Проверка этапа:**

```bash
ssh mufradat 'docker compose version; free -h | grep Swap; sudo ufw status | head -6'
```

Ожидается версия compose v2, 2 ГБ подкачки и открытые 22, 80, 443 — всё без запроса пароля.

---

## Этап 2: Код через GitHub

- [ ] **Шаг 1: Убедиться, что дерево чисто**

На своей машине:

```bash
git status --short
```

Ожидается пусто. На сервер уезжает только закоммиченное: незакоммиченная правка останется
на вашей машине, а стек соберётся из прежнего кода.

- [ ] **Шаг 2: Влить рабочую ветку в `main`**

На своей машине:

```bash
git switch main
git merge --ff-only feat/foundation-and-domain
git log --oneline -1
```

Ожидается последний коммит ветки. `--ff-only` — перемотка: `main` отстаёт на 29 коммитов и
своих не имеет, поэтому merge-коммит не появится и история не перепишется. Если Git
откажется — значит в `main` что-то появилось, остановиться и разобраться.

- [ ] **Шаг 3: Создать приватный репозиторий на GitHub**

Через веб: имя `mufradat-bot`, видимость **Private**, **без** README, `.gitignore` и
лицензии. Пустой нужен потому, что в непустой первый пуш не пройдёт без слияния.

- [ ] **Шаг 4: Убедиться, что секреты не уедут**

```bash
git ls-files .env
```

Ожидается пусто: `.env` в `.gitignore`. Отслеживается только `.env.example` — он с пустыми
значениями.

- [ ] **Шаг 5: Отправить код**

```bash
git remote add origin git@github.com:ВАШ-ЛОГИН/mufradat-bot.git
git push -u origin main
```

Если пуш просит логин и пароль — адрес получился по https. Тогда `git remote set-url origin
git@github.com:ВАШ-ЛОГИН/mufradat-bot.git` и проверить свой ключ: `ssh -T git@github.com`
должен ответить приветствием с вашим логином.

- [ ] **Шаг 6: Сделать на сервере ключ для чтения репозитория**

```bash
ssh mufradat
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -C "mufradat-server"
cat ~/.ssh/id_ed25519.pub
```

- [ ] **Шаг 7: Добавить этот ключ в репозиторий**

GitHub → репозиторий → Settings → Deploy keys → Add deploy key. Вставить вывод предыдущего
шага, галочку **Allow write access не ставить**.

Deploy key, а не личный токен: он привязан к одному репозиторию и только на чтение. Если
сервер когда-нибудь утечёт, остальные ваши репозитории это не затронет.

- [ ] **Шаг 8: Клонировать код**

```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts
git clone git@github.com:ВАШ-ЛОГИН/mufradat-bot.git ~/mufradat
ls -l ~/mufradat/backend/docker-entrypoint.sh
```

`ssh-keyscan` избавляет от вопроса про доверие хосту. Ожидается `-rwxr-xr-x`: исполняемый
бит хранится в git (`100755`). Если его нет — стек не поднимется, а ошибка будет про OCI
runtime, а не про права; лечится `chmod +x`.

**Проверка этапа:**

```bash
ssh mufradat 'cd ~/mufradat && git log --oneline -1 && ls Caddyfile docker-compose.prod.yml'
```

Ожидается тот же коммит, что на своей машине, и оба файла на месте.

---

## Этап 3: Ключи и `.env`

- [ ] **Шаг 1: Перевыпустить токен бота**

У @BotFather: `/revoke` → выбрать бота. Токен светился в выводе терминала при отладке, на
сервер должен поехать новый. Старый токен в локальном `.env` после этого мёртв — локальный
бот перестанет запускаться, это ожидаемо.

- [ ] **Шаг 2: Сгенерировать пароль базы и ключ Django**

```bash
ssh mufradat
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_hex(24))"
python3 -c "import secrets; print('DJANGO_SECRET_KEY=' + secrets.token_urlsafe(64))"
```

Только буквы, цифры, `-` и `_`: значения с `$` или `#` compose разберёт неверно. Ключ
Django на сервере новый, локальный не переносится.

- [ ] **Шаг 3: Написать `.env`**

```bash
nano ~/mufradat/.env
```

Содержимое (`WEBAPP_URL` пока пустой — он появится на этапе 6):

```
POSTGRES_USER=mufradat
POSTGRES_PASSWORD=из шага 2
POSTGRES_NAME=mufradat
POSTGRES_HOST=db
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=из шага 2
DJANGO_DEBUG=false

BOT_TOKEN=новый токен из шага 1
ADMIN_TELEGRAM_ID=ваш telegram id
WEBAPP_URL=

DOMAIN=ВАШ-ДОМЕН.ru
```

```bash
chmod 600 ~/mufradat/.env
```

**Проверка этапа:**

```bash
ssh mufradat 'grep -c . ~/mufradat/.env; stat -c %a ~/mufradat/.env; cd ~/mufradat && git status --short'
```

Ожидается: 11 заполненных строк, права `600` и пустой `git status` — `.env` в `.gitignore`,
поэтому в отслеживаемых он не появился.

---

## Этап 4: Первый подъём стека

- [ ] **Шаг 1: Собрать и поднять**

```bash
ssh mufradat
cd ~/mufradat
docker compose -f docker-compose.prod.yml up -d --build
```

На двух общих ядрах сборка идёт минуты: `uv sync`, затем `npm ci` и `vite build`.

- [ ] **Шаг 2: Проверить состояние контейнеров**

```bash
docker compose -f docker-compose.prod.yml ps
```

Ожидается четыре сервиса в `running`, `db` — `healthy`.

- [ ] **Шаг 3: Проверить, что миграция и статика прошли**

```bash
docker compose -f docker-compose.prod.yml logs backend | tail -30
```

Ожидается: применена `vocabulary.0001_initial` (миграция теперь одна) и системные миграции
Django, «около 157 static files copied», три воркера gunicorn. Миграции запускаются только у
`backend` — проверка `$1 = gunicorn` в точке входа; у `bot` их нет, иначе два `migrate`
пошли бы одновременно на одну базу.

- [ ] **Шаг 4: Проверить бота**

```bash
docker compose -f docker-compose.prod.yml logs bot | tail -5
```

Ожидается `Бот @имя запущен`. Если `TelegramConflictError` — тот же токен поллит кто-то ещё.

- [ ] **Шаг 5: Проверить сертификат**

```bash
docker compose -f docker-compose.prod.yml logs caddy | grep -i "certificate obtained"
```

Ожидается строка о полученном сертификате. Если её нет — не доехал этап 0: либо DNS ещё не
распространился, либо 80-й закрыт в панели Selectel.

- [ ] **Шаг 6: Проверить снаружи**

На своей машине:

```bash
curl -sI https://ВАШ-ДОМЕН.ru | head -1
curl -s https://ВАШ-ДОМЕН.ru/api/v1/entries/
curl -sI https://ВАШ-ДОМЕН.ru/admin/login/ | head -1
```

Ожидается `HTTP/2 200`, пустой список `[]` — колода пока пустая, так и задумано — и `200` у
админки.

**Проверка этапа:** открыть `https://ВАШ-ДОМЕН.ru` в браузере — начальный экран приложения
с одной кнопкой. Открыть `https://ВАШ-ДОМЕН.ru/admin/` — форма входа **со стилями**: они
идут файлами через `/s/`, и если вид «поехал», значит не собралась статика.

---

## Этап 5: Администратор и проверка картинок

- [ ] **Шаг 1: Создать администратора админки**

```bash
ssh mufradat
cd ~/mufradat
docker compose -f docker-compose.prod.yml exec backend python backend/manage.py createsuperuser
```

- [ ] **Шаг 2: Добавить пробное слово с картинкой**

Войти в `https://ВАШ-ДОМЕН.ru/admin/`, добавить одно слово и приложить любую картинку.

Это единственная проверка тома `media`: том пустой, картинок пока нет, а разъезд схемы
адреса (`http` вместо `https`) виден только на настоящем файле.

- [ ] **Шаг 3: Убедиться, что картинка отдаётся**

На своей машине:

```bash
curl -s https://ВАШ-ДОМЕН.ru/api/v1/entries/ | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d), d[0]['image'])"
```

Ожидается `1` и адрес, начинающийся с `https://ВАШ-ДОМЕН.ru/m/entries/`. Схема именно
`https` — за это отвечает `SECURE_PROXY_SSL_HEADER`. Открыть этот адрес в браузере:
картинка должна отдаться.

- [ ] **Шаг 4: Удалить пробное слово**

Через админку. Колоду владелец наберёт заново, когда всё будет готово.

**Проверка этапа:** `curl -s https://ВАШ-ДОМЕН.ru/api/v1/entries/` снова отдаёт `[]`.

---

## Этап 6: Кнопка приложения в боте

- [ ] **Шаг 1: Прописать адрес приложения**

```bash
ssh mufradat
nano ~/mufradat/.env
```

Заменить `WEBAPP_URL=` на `WEBAPP_URL=https://ВАШ-ДОМЕН.ru` — без косой черты на конце.

- [ ] **Шаг 2: Перезапустить бота с новым окружением**

```bash
cd ~/mufradat
docker compose -f docker-compose.prod.yml up -d --force-recreate bot
docker compose -f docker-compose.prod.yml logs bot | tail -3
```

`--force-recreate` — чтобы контейнер точно перечитал `.env`. Кнопка появится сама: это
заложено в `keyboards.open_app`, отдельной настройки у @BotFather не нужно.

- [ ] **Шаг 3: Наполнить колоду через бота**

В Telegram: `/start`, затем отправить боту несколько слов строками — хоть все сразу одним
сообщением.

**Проверка этапа:** в боте есть кнопка открытия приложения; приложение открывается, прогон
идёт по только что добавленным словам, карточка переворачивается, тёмная тема не ломает вид.
Кнопки «Новые слова» и «Фразы» отдают промпты.

---

## Обновления кода потом

На своей машине: закоммитить, `git push`. На сервере:

```bash
ssh mufradat
cd ~/mufradat
git pull
docker compose -f docker-compose.prod.yml up -d --build backend bot   # правки python
docker compose -f docker-compose.prod.yml up -d --build caddy         # правки фронтенда
```

Пересобирать `backend` и `bot` вместе: образ у них общий, и одиночная пересборка оставит
второй сервис на старом коде.

---

## Если что-то пошло не так

| Симптом | Причина и что делать |
|---|---|
| Сертификат не выпускается | DNS не распространился либо 80-й закрыт в панели Selectel. `dig +short домен`, затем `logs caddy` |
| `TelegramConflictError` в логах бота | тот же токен поллит кто-то ещё. Остановить локальный `runbot`: `pkill -f runbot` |
| Сборка падает без внятной ошибки | не хватило памяти. `free -h` — подкачка из этапа 1 должна быть включена |
| `git clone` просит пароль | deploy key не добавлен или добавлен не в тот репозиторий. Проверить `ssh -T git@github.com` с сервера |
| Админка без стилей | не собралась статика. `logs backend` на строку про static files, при необходимости `up -d --build backend bot` |
| Картинка не грузится на https-странице | схема уехала на `http`. Проверить `SECURE_PROXY_SSL_HEADER` и что запрос идёт через Caddy, а не мимо |
| Поправили python — на сервере старый код | пересобраны не оба сервиса. Всегда `up -d --build backend bot` |
| Поправили фронтенд — ничего не изменилось | нужен `up -d --build caddy`: `dist` лежит внутри образа Caddy |
| Локальный бот больше не запускается | так и должно быть после `/revoke`. Для локальной отладки — отдельный тестовый бот со своим токеном |

---

## Чего в плане нет

- **Переноса колоды.** Решение владельца: наберёт заново через бота, когда всё будет
  готово. Локальные 22 карточки и `backend/media/` остаются на его машине.
- **Резервного копирования.** Решение владельца: не нужно. Честный риск: колода будет жить
  только на сервере, и при потере диска восстанавливать её будет нечем.
- **Наблюдения за живостью.** `restart: always` поднимает упавший контейнер сам; внешнего
  следящего нет, о простое никто не сообщит.
