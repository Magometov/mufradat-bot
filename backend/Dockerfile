# Pillow ставится из исходников, ради raqm: без него огласовки на карточке-картинке
# съезжают с букв. Сборка — отдельным этапом, чтобы компилятор не остался в образе.
FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc python3-dev libraqm-dev libfreetype-dev libjpeg-dev libwebp-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group backend


FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Библиотеки, с которыми собран Pillow: сам он приезжает готовым из этапа выше.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libraqm0 libfreetype6 libjpeg62-turbo zlib1g \
      libwebp7 libwebpdemux2 libwebpmux3 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local /usr/local

WORKDIR /app

# Содержимое backend/ ложится прямо в /app: внутри образа вложенность ни к чему,
# manage.py вызывается без пути, а gunicorn — без --chdir.
COPY backend/ ./

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
