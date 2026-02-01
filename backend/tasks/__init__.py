"""Celery tasks initialization."""

from celery import Celery
from backend.config import settings

# Create Celery app
celery_app = Celery(
    "supply_chain_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Import tasks explicitly to ensure they are registered
from backend.tasks import document_tasks  # noqa

# Auto-discover tasks
celery_app.autodiscover_tasks(['backend.tasks'])
