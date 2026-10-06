"""Celery Beat scheduling configuration.

Defines crontab and interval-based periodic tasks on the app from
celery_app.py (installed in your project as myapp.celery_app).
"""

from datetime import timedelta

from celery.schedules import crontab

from myapp.celery_app import app

# Set timezone for all scheduled tasks
app.conf.timezone = "UTC"

app.conf.beat_schedule = {
    # Interval-based: run every 10 minutes
    "cleanup-temp-files": {
        "task": "tasks.cleanup_temp_files",
        "schedule": timedelta(minutes=10),
    },
    # Crontab: daily at 3:00 AM UTC
    "daily-report": {
        "task": "tasks.generate_daily_report",
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {"report_type": "daily"},
    },
    # Crontab: every Monday at 9:00 AM UTC
    "weekly-digest": {
        "task": "tasks.send_weekly_digest",
        "schedule": crontab(hour=9, minute=0, day_of_week="monday"),
    },
    # Crontab: every hour on weekdays
    "sync-inventory": {
        "task": "tasks.sync_inventory",
        "schedule": crontab(minute=0, hour="9-17", day_of_week="1-5"),
    },
    # Route scheduled tasks to specific queues
    "nightly-batch": {
        "task": "tasks.run_nightly_batch",
        "schedule": crontab(hour=2, minute=30),
        "options": {"queue": "bulk"},
    },
}
