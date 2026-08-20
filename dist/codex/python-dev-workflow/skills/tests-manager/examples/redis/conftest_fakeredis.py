"""Example conftest.py for unit tests using fakeredis (no real Redis needed)."""

import pytest
import fakeredis


@pytest.fixture
def redis_client():
    """In-memory Redis mock -- fast, isolated, no external dependencies."""
    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    client.flushall()
    client.close()


@pytest.fixture
def cache_service(redis_client):
    """Inject fakeredis into the service under test."""
    from app.cache import CacheService

    return CacheService(client=redis_client)
