#!/bin/sh
# Start script for the monAI image. The web server (gunicorn) applies the
# database migrations first; other commands (for example bill-alerts.sh) run as given.
set -e

if [ "$1" = "gunicorn" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
