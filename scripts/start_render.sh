#!/usr/bin/env bash
# Start Gunicorn bound to 0.0.0.0 and Render's PORT (required for Render.com).
set -e
PORT="${PORT:-8000}"
exec gunicorn budget_tracker.wsgi:application --bind "0.0.0.0:${PORT}"
