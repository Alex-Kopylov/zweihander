"""
Task definition patterns: retry with backoff, batch chunking, idempotency.

All tasks use bind=True, JSON serialization, and proper time limits.
"""

import logging

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded

app = Celery('tasks', broker='redis://localhost:6379/0')
logger = logging.getLogger(__name__)


# --- Pattern 1: Task with manual retry and exponential backoff ---

@app.task(
    bind=True,
    name='tasks.process_order',
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=300,
    soft_time_limit=240,
    rate_limit='100/m',
)
def process_order(self, order_id: int):
    """Process order with idempotency check and structured error handling."""
    try:
        logger.info("Processing order", extra={'task_id': self.request.id, 'order_id': order_id})

        order = get_order(order_id)
        if order.status == 'processed':
            return {'order_id': order_id, 'status': 'already_processed'}

        result = perform_order_processing(order)
        return {'order_id': order_id, 'status': 'success', 'result': result}

    except SoftTimeLimitExceeded:
        cleanup_processing(order_id)
        raise
    except TemporaryError as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    except PermanentError as exc:
        send_failure_notification(order_id, str(exc))
        raise


# --- Pattern 2: Auto-retry with backoff for external API calls ---

@app.task(
    bind=True,
    max_retries=5,
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    time_limit=60,
    soft_time_limit=50,
)
def call_external_api(self, url: str):
    """Auto-retry on RequestException with exponential backoff + jitter."""
    import requests

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


# --- Pattern 3: Batch chunking for bulk processing ---

@app.task(
    bind=True,
    time_limit=600,
    soft_time_limit=540,
    acks_late=True,
)
def process_batch(self, item_ids: list[int]):
    """Process items in chunks for efficiency. Dispatch with:

    for chunk in chunks(all_item_ids, size=100):
        process_batch.delay(chunk)
    """
    results = []
    for item_id in item_ids:
        try:
            result = process_single_item(item_id)
            results.append({'item_id': item_id, 'status': 'success', 'result': result})
        except Exception as exc:
            logger.warning("Failed to process item", extra={'item_id': item_id, 'error': str(exc)})
            results.append({'item_id': item_id, 'status': 'failed', 'error': str(exc)})
    return results
