"""Pytest setup for Celery live-worker integration tests.

Copy this into the project's tests/conftest.py. It is named conftest_celery.py
here so pytest does not load it as a real conftest while collecting this
repository; pytest_plugins only works from an initial conftest.

The in-memory defaults keep local tests lightweight; set CELERY_BROKER_URL and
CELERY_RESULT_BACKEND when the transport or backend is part of the behavior
under test.
"""

import os

import pytest


pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": os.getenv("CELERY_BROKER_URL", "memory://"),
        "result_backend": os.getenv(
            "CELERY_RESULT_BACKEND",
            "cache+memory://",
        ),
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
    }


@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {"shutdown_timeout": 15}
