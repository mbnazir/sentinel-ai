from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "sentinel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    result_expires=86400,
)
