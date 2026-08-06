FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ backend/

ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
CMD ["gunicorn", "--chdir", "backend", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "3"]
