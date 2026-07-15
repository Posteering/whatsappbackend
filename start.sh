#!/bin/bash
# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info --concurrency=2 &

# Start Celery beat in the background
echo "Starting Celery beat..."
celery -A app.core.celery_app beat --loglevel=info &

# Start Uvicorn in the foreground
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
