#!/bin/bash
set -e

echo "Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info --concurrency=2 &

echo "Starting Celery beat..."
celery -A app.core.celery_app beat --loglevel=info &

echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
