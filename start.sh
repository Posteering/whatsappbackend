#!/bin/bash

# 1. Force Celery to allow running as root inside the container
export C_FORCE_ROOT=1

# 2. Start the Celery worker in the background
celery -A app.core.celery_app worker --loglevel=info &

# 3. Start the Celery beat scheduler in the background (optional, but needed for reminders)
celery -A app.core.celery_app beat --loglevel=info &

# 4. Start your FastAPI/Uvicorn web server in the foreground
# Railway automatically provides the $PORT variable, so we bind to it
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
