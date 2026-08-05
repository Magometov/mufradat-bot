from os import getenv
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env лежит в корне репозитория, на уровень выше backend/.
# Уже заданные переменные не перезаписываются: в Docker побеждает реальное окружение.
load_dotenv(BASE_DIR.parent / ".env")

SECRET_KEY = getenv("DJANGO_SECRET_KEY")
DEBUG = getenv("DJANGO_DEBUG", "").lower() == "true"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # apps
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

# Те же переменные читает docker-compose, поэтому данные БД живут только в .env.
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

# --- Telegram и ИИ ---------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_TELEGRAM_IDS = [int(x) for x in getenv("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip()]
WEBAPP_URL = getenv("WEBAPP_URL")

ANTHROPIC_API_KEY = getenv("ANTHROPIC_API_KEY", default="")
AI_MODEL = getenv("AI_MODEL") or "claude-sonnet-5"
