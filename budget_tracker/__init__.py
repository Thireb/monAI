"""Project package; exposes the Celery app for Django."""

from __future__ import annotations

from .celery import app as celery_app

__all__ = ("celery_app",)
