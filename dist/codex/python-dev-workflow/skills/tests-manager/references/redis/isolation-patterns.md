# Redis Test Isolation Patterns

## Key Prefix Wrapper

A lightweight wrapper that auto-prefixes keys for safe parallel runs on shared Redis.

```python
# tests/conftest.py
import pytest
import uuid

@pytest.fixture(scope="session")
def test_prefix():
    return f"test:{uuid.uuid4().hex[:8]}:"

@pytest.fixture
def prefixed_client(redis_client, test_prefix):
    import redis

    class PrefixedRedis:
        def __init__(self, client: redis.Redis, prefix: str) -> None:
            self._client = client
            self._prefix = prefix

        def _prefixed(self, key: str) -> str:
            return f"{self._prefix}{key}"

        def set(self, key: str, value: str, **kwargs) -> bool:
            return self._client.set(self._prefixed(key), value, **kwargs)

        def get(self, key: str) -> str | None:
            return self._client.get(self._prefixed(key))

        def delete(self, *keys: str) -> int:
            prefixed_keys = [self._prefixed(k) for k in keys]
            return self._client.delete(*prefixed_keys)

        def keys(self, pattern: str = "*") -> list[str]:
            return self._client.keys(f"{self._prefix}{pattern}")

        def cleanup(self) -> None:
            matched = self._client.keys(f"{self._prefix}*")
            if matched:
                self._client.delete(*matched)

    client = PrefixedRedis(client=redis_client, prefix=test_prefix)
    yield client
    client.cleanup()
```

## Database-Per-Suite Rotation

Assign each test class a unique DB index (1-14) for parallel suites without Docker.

```python
# tests/conftest.py
import pytest
import redis

_next_db = 1

@pytest.fixture(scope="class")
def redis_db():
    global _next_db
    db = _next_db
    _next_db = (_next_db % 14) + 1  # rotate through DB 1-14

    client = redis.Redis(
        host="localhost",
        port=6379,
        db=db,
        decode_responses=True,
    )
    client.flushdb()
    yield client
    client.flushdb()
    client.close()
```

## Choosing an Isolation Strategy

| Scenario | Recommended Strategy |
|---|---|
| Single dev, Redis running locally | Separate DB (`db=15`) |
| Parallel CI jobs sharing one Redis | Key prefix with UUID |
| Full isolation, Docker available | Testcontainers (session-scoped) |
| No external services allowed | fakeredis |

### Combining strategies

For maximum safety in CI, combine testcontainers with auto-flush:

```python
@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as container:
        yield container

@pytest.fixture(scope="session")
def redis_client(redis_container):
    client = redis.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        decode_responses=True,
    )
    yield client
    client.close()

@pytest.fixture(autouse=True)
def clean_redis(redis_client):
    redis_client.flushall()
    yield
```

This gives full isolation (dedicated container) plus clean state per test (autouse flush).
