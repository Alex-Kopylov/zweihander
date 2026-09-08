"""
Celery app factory with Redis broker.

Usage:
    from myapp.celery_app import app

    # Or as a module:
    # celery -A myapp.celery_app worker --loglevel=info
"""

import os

from celery import Celery

app = Celery('myapp')

app.conf.update(
    # Broker (Redis)
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,

    # Result backend (Redis, separate DB to isolate from broker)
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    result_expires=3600,

    # Serialization — JSON only, never pickle
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Task defaults
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_track_started=True,

    # Worker
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_hijack_root_logger=False,
)

# Auto-discover tasks from installed apps
app.autodiscover_tasks(['myapp'])
