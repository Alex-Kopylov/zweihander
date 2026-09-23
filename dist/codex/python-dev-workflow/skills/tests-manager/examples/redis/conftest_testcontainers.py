"""Example conftest.py for integration tests using testcontainers (real Redis in Docker)."""

import pytest
import redis
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def redis_container():
    """Start a disposable Redis container for the entire test session."""
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def redis_client(redis_container):
    """Create a redis-py client connected to the test container."""
    client = redis.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        decode_responses=True,
    )
    yield client
    client.close()


@pytest.fixture(autouse=True)
def clean_redis(redis_client):
    """Flush all data before each test for a clean slate."""
    redis_client.flushall()
    yield


@pytest.fixture
def cache_service(redis_client):
    """Inject the real Redis client into the service under test."""
    from app.cache import CacheService

    return CacheService(client=redis_client)
