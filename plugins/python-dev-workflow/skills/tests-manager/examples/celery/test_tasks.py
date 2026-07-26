"""Examples of Celery task unit and live-worker integration tests."""

from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from myapp.tasks import process_order


class TestProcessOrder:
    @patch("myapp.tasks.perform_order_processing")
    def test_task_delegates_order_to_service(self, process_order_mock):
        process_order_mock.return_value = {"status": "success"}

        result = process_order(order_id=123)

        process_order_mock.assert_called_once_with(order_id=123)
        assert result == {"status": "success"}

    @patch("myapp.tasks.process_order.retry")
    @patch("myapp.tasks.perform_order_processing")
    def test_retryable_failure_raises_retry(self, process_order_mock, retry_mock):
        process_order_mock.side_effect = ConnectionError("timeout")
        retry_mock.side_effect = Retry()

        with pytest.raises(Retry):
            process_order(order_id=123)

        retry_mock.assert_called_once()


def test_task_runs_through_worker(celery_app, celery_worker):
    @celery_app.task
    def add(left, right):
        return left + right

    celery_worker.reload()

    assert add.delay(4, 4).get(timeout=10) == 8
