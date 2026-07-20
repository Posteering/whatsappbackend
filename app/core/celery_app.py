from celery import Celery
from app.core.config import settings

# Build SSL options if the Redis URL uses the TLS rediss:// scheme
_redis_url = settings.REDIS_URL
_use_ssl = _redis_url.startswith("rediss://")

_ssl_options = {"ssl_cert_reqs": "none"} if _use_ssl else {}

celery_app = Celery(
    "worker",
    broker=_redis_url,
    backend=_redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # SSL options for TLS Redis (rediss://) — required for Upstash
    broker_use_ssl=_ssl_options if _use_ssl else None,
    redis_backend_use_ssl=_ssl_options if _use_ssl else None,
    redis_backend_health_check_interval=30,
    broker_transport_options={
        "health_check_interval": 30,
        **({"ssl_cert_reqs": "none"} if _use_ssl else {}),
    },
    beat_schedule={
        'send-payment-reminders-every-hour': {
            'task': 'app.services.background_tasks.send_payment_reminders_task',
            'schedule': 3600.0,  # Every 60 minutes
        },
    }
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["app.services"], related_name="background_tasks")
