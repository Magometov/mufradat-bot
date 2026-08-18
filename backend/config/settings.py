from os import getenv
from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = getenv("DJANGO_SECRET_KEY")
DEBUG = getenv("DJANGO_DEBUG", "").lower() == "true"

ALLOWED_HOSTS = [host.strip() for host in (getenv("ALLOWED_HOSTS") or "*").split(",")]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    # apps
    "apps.common",
    "apps.learning",
    "apps.vocabulary",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("POSTGRES_NAME", "postgres"),
        "USER": getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": getenv("POSTGRES_PASSWORD"),
        "HOST": getenv("POSTGRES_HOST", "db"),
        "PORT": getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 600,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
USE_I18N = True
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
LANGUAGES = (("ru", _("Russian")), ("en", _("English")))

STATIC_URL = "/s/"
STATIC_ROOT = Path(BASE_DIR) / "static"

MEDIA_URL = "/m/"
MEDIA_ROOT = Path(BASE_DIR) / "media"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {"apps": {"handlers": ["console"], "level": "INFO"}},
}

# --- Пределы открытых ручек -----------------------------------------------------
# Без них журнал входов и прогресс можно засорять сколько угодно.

# Частота запросов; считается по адресу, потому что опознание у ручек разное.
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "visits": getenv("VISITS_RATE") or "60/hour",
        "answers": getenv("ANSWERS_RATE") or "120/hour",
    },
}
# Столько оценок принимается за раз: пачка собирается в браузере и уезжает разом.
ANSWERS_LIMIT = int(getenv("ANSWERS_LIMIT") or 100)

# --- Telegram -------------------------------------------------------------------

# Общий секрет с ботом: им подписаны служебные ручки, через которые бот пишет карточки
# в колоду. Пустой секрет не пускает никого — иначе ручки открыты всем.
BOT_API_TOKEN = getenv("BOT_API_TOKEN")
# Токен бота: им Telegram подписывает данные о том, кто открыл приложение. Без сверки
# подписи id и ник значили бы не больше, чем присланная кем угодно строка.
BOT_TOKEN = getenv("BOT_TOKEN")
# Владелец: его заходы не пишутся в журнал, чтобы не мешали считать чужие, и ему одному
# бот показывает команду добавления карточек.
ADMIN_TELEGRAM_ID = int(getenv("ADMIN_TELEGRAM_ID") or 0)

# --- Повторение по расписанию ---------------------------------------------------
# Числа подкручиваются по опыту, поэтому живут в окружении, а не в коде. Приложение
# получает их вместе с состоянием прогресса и собирает по ним сеанс.

# Лестница сроков в днях: уровень 1 — через день, последний — через 35.
LADDER = [int(days) for days in (getenv("LADDER") or "1,3,7,16,35").split(",")]
# Разброс к каждому сроку в процентах, чтобы раздел не возвращался лавиной.
JITTER_PERCENT = int(getenv("JITTER_PERCENT") or 10)
# Куда уезжает новая карточка, узнанная сразу: «знал заранее» — не «вспомнил с третьего раза».
FIRST_SIGHT_LEVEL = int(getenv("FIRST_SIGHT_LEVEL") or 3)
# Потолок сеанса у кнопки «Повторить» и сколько новых карточек в него попадает.
# В сеансе, набранном заходом в раздел, потолка нет.
SESSION_LIMIT = int(getenv("SESSION_LIMIT") or 20)
NEW_LIMIT = int(getenv("NEW_LIMIT") or 10)
# Открыть новую логику всем, а не только тем, кому поставили галочку в админке.
# TODO: когда логика открыта всем и это устоялось — снести саму переменную вместе с
# галочкой `Learner.scheduling`, признаком `enabled` в ответе API и ветками во фронтенде.
SCHEDULING_FOR_ALL = getenv("SCHEDULING_FOR_ALL", "").lower() == "true"

# --- Слово в группу -------------------------------------------------------------
# Куда шлём. У супергруппы id отрицательный; пустой — рассылки нет вовсе.
GROUP_CHAT_ID = int(getenv("GROUP_CHAT_ID") or 0)

# --- Картинки в облаке ------------------------------------------------------------
# Серверы Telegram до нашего хостинга не доходят: вместо картинки они получают
# страницу-заглушку и отвечают «wrong type of the web page content». Поэтому картинки
# лежат в Cloudflare R2 и раздаются с его адреса — туда Telegram доходит.

# Куда класть: s3://ключ:секрет@<account>.r2.cloudflarestorage.com/бакет.
# Пусто — картинки остаются на диске: так живут своя машина и тесты.
BUCKET_URL = getenv("BUCKET_URL", "")
# Откуда брать: публичный адрес бакета, его видят и приложение, и Telegram.
BUCKET_PUBLIC_URL = getenv("BUCKET_PUBLIC_URL", "")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

if BUCKET_URL:
    # Имя с подчёркиванием — не настройка, а разобранная строка доступа.
    _bucket = urlsplit(BUCKET_URL)
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": _bucket.path.strip("/"),
            "endpoint_url": f"https://{_bucket.hostname}",
            "access_key": unquote(_bucket.username or ""),
            "secret_key": unquote(_bucket.password or ""),
            # Адреса в ответах строятся от публичного домена, а не от служебного.
            "custom_domain": BUCKET_PUBLIC_URL.removeprefix("https://").rstrip("/"),
            # Ссылки без подписи: колода и так открыта, а подписанная живёт считаные
            # часы — Telegram по такой второй раз не придёт.
            "querystring_auth": False,
            # У R2 регион один и называется так.
            "region_name": "auto",
        },
    }
