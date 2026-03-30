"""
Pytest fixtures for testing Celery tasks.

Provides both eager-mode fixtures (fast unit tests, no broker required)
and integration-mode fixtures (real Redis broker).
"""

import pytest


# --- Eager Mode (Unit Tests) ---

@pytest.fixture
def celery_config():
    """Configure Celery for eager execution — tasks run synchronously in-process.

    No broker or result backend needed. Use for unit tests.
    """
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,
        'task_eager_propagates': True,
    }


# --- Integration Mode (Real Broker) ---

@pytest.fixture(scope='session')
def celery_config_integration():
    """Configure Celery with a real Redis broker for integration tests.

    Requires a running Redis instance.
    Mark tests with @pytest.mark.integration.
    """
    import os

    return {
        'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/15'),
        'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/14'),
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
    }


# --- Test Examples ---

class TestProcessOrder:
    """Example test class using eager-mode fixtures."""

    def test_success(self, celery_app, celery_worker):
        from myapp.tasks import process_order

        result = process_order.delay(order_id=123)
        assert result.get(timeout=10) == {'order_id': 123, 'status': 'success'}

    def test_idempotent(self, celery_app, celery_worker):
        from myapp.tasks import process_order

        result1 = process_order.delay(order_id=123).get(timeout=10)
        result2 = process_order.delay(order_id=123).get(timeout=10)
        assert result1['status'] in ['success', 'already_processed']
        assert result2['status'] in ['success', 'already_processed']

    def test_retry_on_failure(self, celery_app, celery_worker, mocker):
        from myapp.tasks import process_order

        mock_process = mocker.patch('myapp.tasks.perform_order_processing')
        mock_process.side_effect = [TemporaryError("Timeout"), {'result': 'ok'}]

        result = process_order.delay(order_id=123)
        assert result.get(timeout=10)['status'] == 'success'
        assert mock_process.call_count == 2
