"""Task definition patterns: retry with backoff, batch chunking, idempotency.

Every task sets time limits and inherits JSON serialization from the app in
celery_app.py; bind=True is used where the task reads its own request or
retries itself. The myapp.* imports stand for your project's own modules.
"""

import logging

import requests
from celery.exceptions import SoftTimeLimitExceeded

from myapp.celery_app import app
from myapp.errors import PermanentError, TemporaryError
from myapp.orders import (
    cleanup_processing,
    get_order,
    perform_order_processing,
    process_single_item,
    send_failure_notification,
)

logger = logging.getLogger(__name__)


# --- Pattern 1: Task with manual retry and exponential backoff ---


@app.task(
    bind=True,
    name="tasks.process_order",
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=300,
    soft_time_limit=240,
    rate_limit="100/m",
)
def process_order(self, order_id: int):
    """Process order with idempotency check and structured error handling."""
    try:
        logger.info("Processing order", extra={"task_id": self.request.id, "order_id": order_id})

        order = get_order(order_id)
        if order.status == "processed":
            return {"order_id": order_id, "status": "already_processed"}

        result = perform_order_processing(order)
    except SoftTimeLimitExceeded:
        cleanup_processing(order_id)
        raise
    except TemporaryError as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc
    except PermanentError as exc:
        send_failure_notification(order_id, str(exc))
        raise
    return {"order_id": order_id, "status": "success", "result": result}


# --- Pattern 2: Auto-retry with backoff for external API calls ---


@app.task(
    max_retries=5,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    time_limit=60,
    soft_time_limit=50,
)
def call_external_api(url: str):
    """Auto-retry on RequestException with exponential backoff + jitter."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


# --- Pattern 3: Batch chunking for bulk processing ---


@app.task(
    time_limit=600,
    soft_time_limit=540,
    acks_late=True,
)
def process_batch(item_ids: list[int]):
    """Process items in chunks for efficiency.

    One failing item is recorded and does not fail the batch; an unexpected
    error still fails the task. Dispatch with:

        for chunk in chunks(all_item_ids, size=100):
            process_batch.delay(chunk)
    """
    results = []
    for item_id in item_ids:
        try:
            result = process_single_item(item_id)
            results.append({"item_id": item_id, "status": "success", "result": result})
        except (TemporaryError, PermanentError) as exc:
            logger.warning("Failed to process item", extra={"item_id": item_id, "error": str(exc)})
            results.append({"item_id": item_id, "status": "failed", "error": str(exc)})
    return results
