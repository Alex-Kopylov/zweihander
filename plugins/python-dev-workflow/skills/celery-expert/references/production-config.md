# Production Configuration

## Complete Redis Configuration

```python
import os
from celery import Celery
from kombu import Exchange, Queue

app = Celery('myapp')

app.conf.update(
    # --- Broker (Redis) ---
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,
    broker_transport_options={
        'visibility_timeout': 3600,  # must exceed longest task time_limit
        'socket_keepalive': True,
        'retry_on_timeout': True,
    },

    # --- Result Backend (Redis, separate DB) ---
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    result_expires=3600,

    # --- Serialization (JSON only, never pickle) ---
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # --- Task Defaults ---
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_track_started=True,

    # --- Worker ---
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_hijack_root_logger=False,

    # --- Queue Routing ---
    task_queues=(
        Queue('critical', Exchange('critical'), routing_key='critical'),
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('bulk', Exchange('bulk'), routing_key='bulk'),
    ),
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)
```

## Redis with TLS

```python
app.conf.broker_url = 'rediss://:password@redis.example.com:6380/0'
app.conf.broker_use_ssl = {
    'ssl_cert_reqs': 'required',
    'ssl_ca_certs': '/path/to/ca.pem',
    'ssl_certfile': '/path/to/client.pem',
    'ssl_keyfile': '/path/to/client.key',
}
# Same for result backend if using Redis
app.conf.redis_backend_use_ssl = app.conf.broker_use_ssl
```

Note: use `rediss://` (double s) for TLS connections.

## Celery Beat Scheduling

```python
from celery.schedules import crontab
from datetime import timedelta

app.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'tasks.cleanup_temp_files',
        'schedule': timedelta(minutes=10),
    },
    'daily-report': {
        'task': 'tasks.generate_daily_report',
        'schedule': crontab(hour=3, minute=0),
        'kwargs': {'report_type': 'daily'},
    },
    'weekly-digest': {
        'task': 'tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),
    },
}

app.conf.timezone = 'UTC'
```

### Beat with Database Scheduler

For multi-instance deployments, use `django-celery-beat` or `celery-redbeat` to store the schedule in a database or Redis (prevents duplicate task dispatching):

```bash
# Using celery-redbeat (stores schedule in Redis)
pip install celery-redbeat
celery -A app beat -S redbeat.RedBeatScheduler
```

### Preventing Duplicate Scheduled Tasks

Use a distributed lock to ensure only one beat scheduler runs:

```python
from celery_redbeat import RedBeatSchedulerEntry

# RedBeat handles locking automatically via Redis
# Just run: celery -A app beat -S redbeat.RedBeatScheduler
```

## Worker Deployment

### Systemd Service

```ini
# /etc/systemd/system/celery-worker.service
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=celery
Group=celery
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/.venv/bin/celery -A myapp multi start worker \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log \
    --loglevel=INFO \
    -Q default,critical \
    --concurrency=4
ExecStop=/opt/myapp/.venv/bin/celery -A myapp multi stopwait worker \
    --pidfile=/var/run/celery/%n.pid
ExecReload=/opt/myapp/.venv/bin/celery -A myapp multi restart worker \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Entrypoint

```dockerfile
# Worker
CMD ["celery", "-A", "myapp", "worker", "--loglevel=info", "--concurrency=4", "-Q", "default,critical"]

# Beat
CMD ["celery", "-A", "myapp", "beat", "--loglevel=info", "-S", "redbeat.RedBeatScheduler"]
```

## Logging Configuration

```python
import logging

app.conf.worker_hijack_root_logger = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'celery': {'level': 'INFO', 'handlers': ['console']},
        'myapp.tasks': {'level': 'INFO', 'handlers': ['console']},
    },
}
```

## Health Checks

```python
from celery import Celery

def check_celery_health(app: Celery) -> dict:
    """Check broker connectivity and worker availability."""
    inspector = app.control.inspect()
    stats = inspector.stats()
    if not stats:
        return {'healthy': False, 'reason': 'No workers responding'}

    active = inspector.active()
    reserved = inspector.reserved()
    return {
        'healthy': True,
        'workers': len(stats),
        'active_tasks': sum(len(v) for v in (active or {}).values()),
        'reserved_tasks': sum(len(v) for v in (reserved or {}).values()),
    }
```

## Graceful Shutdown

Workers should finish current tasks before stopping. Configure appropriate timeouts:

```bash
# Warm shutdown — wait up to 60s for tasks to finish
celery -A app control shutdown

# In systemd, TimeoutStopSec should exceed your longest task
# TimeoutStopSec=310  (slightly more than task_time_limit=300)
```

Set `worker_max_tasks_per_child` to prevent memory leaks — the worker process restarts after N tasks:

```python
app.conf.worker_max_tasks_per_child = 1000
```
