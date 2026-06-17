"""
Load test the minimal dashboard calendar endpoints.

Prerequisites:
  0. Redis running (calendar cache backend):
       docker compose up redis -d
       # or: redis-server
  1. Django app running (prefer gunicorn with multiple workers for concurrency):
       uv run gunicorn budget_tracker.wsgi:application --workers 4 --bind 0.0.0.0:8000
  2. learning_demo.calendar_query_delay_seconds set in config.yaml (e.g. 2)
  3. Your real account credentials (defaults are placeholders — set env vars):
       export LOCUST_LOGIN_EMAIL=you@example.com
       export LOCUST_LOGIN_PASSWORD=your-password

Run (from project root — locust is in pyproject.toml; use uv so the venv binary is found):
  uv sync
  uv run locust -f loadtests/locustfile.py --host=http://127.0.0.1:8000

Tip: first requests per year are slow (cache miss); re-run the swarm to see Redis cache hits
      drop median latency from ~20s to tens of milliseconds.

Or activate the venv first:
  source .venv/bin/activate
  locust -f loadtests/locustfile.py --host=http://127.0.0.1:8000

Open http://localhost:8089, set users/spawn rate, and start the swarm.
"""

import os
import random
import re
from datetime import date

from locust import HttpUser, between, task


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


LOGIN_EMAIL = _env("LOCUST_LOGIN_EMAIL", "")
LOGIN_PASSWORD = _env("LOCUST_LOGIN_PASSWORD", "")


class DashboardUser(HttpUser):
    """Simulates logged-in users browsing the home calendar."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        self._login()

    def _login(self) -> None:
        if not LOGIN_EMAIL or not LOGIN_PASSWORD:
            raise RuntimeError(
                "Set LOCUST_LOGIN_EMAIL and LOCUST_LOGIN_PASSWORD to a real account "
                "(admin@example.com is not auto-created in this project)."
            )

        login_page = self.client.get("/accounts/login/", name="GET /accounts/login/")
        if login_page.status_code != 200:
            raise RuntimeError(f"Login page failed: HTTP {login_page.status_code}")

        csrf_match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            login_page.text,
        )
        if not csrf_match:
            raise RuntimeError("Could not find CSRF token on login page")

        csrf_token = csrf_match.group(1)
        with self.client.post(
            "/accounts/login/",
            data={
                "login": LOGIN_EMAIL,
                "password": LOGIN_PASSWORD,
                "csrfmiddlewaretoken": csrf_token,
            },
            headers={
                "Referer": f"{self.host}/accounts/login/",
                "X-CSRFToken": csrf_token,
            },
            name="POST /accounts/login/",
            catch_response=True,
        ) as response:
            if response.status_code == 403:
                response.failure(
                    "CSRF rejected (403). If testing over plain HTTP, restart Django "
                    "without CAPACITOR_SECURE_COOKIES (default local dev settings)."
                )
                return
            if response.status_code not in (200, 302):
                response.failure(f"Unexpected status {response.status_code}")
                return
            if "sessionid" not in self.client.cookies:
                response.failure(
                    "No session cookie — wrong email/password or account inactive"
                )
                return
            response.success()

    @task(3)
    def load_dashboard(self) -> None:
        """Initial dashboard load (HomeView: 5-year prefetch + pre-render)."""
        year = date.today().year
        self.client.get(f"/minimal/{year}/", name="GET /minimal/<year>/")

    @task(5)
    def load_calendar_year(self) -> None:
        """AJAX calendar fetch for years outside the client-side ±2 cache window."""
        current_year = date.today().year
        uncached_years = [
            current_year - 10,
            current_year - 5,
            current_year + 5,
            current_year + 10,
        ]
        year = random.choice(uncached_years)
        self.client.get(
            f"/minimal/calendar/{year}/",
            name="GET /minimal/calendar/<year>/",
        )

    @task(2)
    def load_calendar_nearby_year(self) -> None:
        """Calendar fetch for a year that may already be cached client-side."""
        year = date.today().year + random.choice([-1, 0, 1])
        self.client.get(
            f"/minimal/calendar/{year}/",
            name="GET /minimal/calendar/<year>/ (nearby)",
        )
