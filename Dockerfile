# monAI: the web app image. See README.md ("Self-host with Docker").
#
# Stage 1 builds the Python packages from uv.lock. Stage 2 has only what the
# app needs to run: the packages, the WeasyPrint (PDF) libraries and the code.

FROM python:3.13-slim-trixie AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv

# mysqlclient and pycairo compile against the MariaDB client and cairo libraries.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential pkg-config default-libmysqlclient-dev libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.13-slim-trixie

# libmariadb3: MySQL/MariaDB client. pango, harfbuzz, cairo, gdk-pixbuf and a
# font: WeasyPrint for the PDF report.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libmariadb3 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
        libcairo2 libgdk-pixbuf-2.0-0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 monai

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_DIR=/app/logs

COPY --from=build /opt/venv /opt/venv

WORKDIR /app
COPY --chown=monai:monai . .

# collectstatic needs settings to load; this key is used only in this build step.
RUN mkdir -p /app/logs \
    && SECRET_KEY=build-only-key-not-used-at-run-time-0123456789abcdef \
    python manage.py collectstatic --noinput \
    && rm -f /app/logs/*.log \
    && chown -R monai:monai /app/staticfiles /app/logs

USER monai

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/', timeout=4)"

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "budget_tracker.wsgi:application", "--bind", "0.0.0.0:8000", \
     "--workers", "3", "--access-logfile", "-"]
