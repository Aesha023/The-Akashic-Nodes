"""Celery worker entrypoint (B1. Platform Core)."""

from __future__ import annotations

from backend.app.core.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()
