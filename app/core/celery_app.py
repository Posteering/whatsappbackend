from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        'send-payment-reminders-every-hour': {
            'task': 'app.services.background_tasks.send_payment_reminders_task',
            'schedule': 3600.0, # Every 60 minutes
        },
    }
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["app.services.background_tasks"])
