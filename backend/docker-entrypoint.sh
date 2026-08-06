#!/bin/sh
set -e

if [ "$1" = "gunicorn" ]; then
    python backend/manage.py migrate --noinput
    python backend/manage.py collectstatic --noinput --clear
fi

exec "$@"
