---
name: pytest-redis
description: This skill should be used when the user asks to "test Redis", "write Redis tests", "add Redis integration tests", "mock Redis in tests", "use fakeredis", "set up testcontainers for Redis", "test pub/sub", "test Lua scripts in Redis", "redis fixture", "redis conftest", or when test code involves redis-py, fakeredis, or testcontainers Redis fixtures.
---

# Testing Redis with pytest

## Overview

Guidance for Redis unit and integration tests in Python projects using pytest: fixtures, isolation, fakeredis, testcontainers, pub/sub, Lua scripts, and concurrency.

## When to Apply

Activate when any of the following appear in test code or user intent:

- `import redis` or `from redis import ...` in test files or fixtures
- `fakeredis`, `testcontainers.redis`, or `RedisContainer` imports
- Fixtures that create a `redis.Redis` client
- Cache/session/queue services backed by Redis under test

## Strategy Decision Matrix

| Strategy | Isolation | Speed | Production Parity | When to Choose |
|---|---|---|---|---|
| **fakeredis** | Full | Fastest | Low | Unit tests, no Docker available, CI speed critical |
| **Separate Redis DB** | Good | Fast | High | Local dev with Redis already running |
| **Testcontainers** | Full | Medium | Highest | Integration tests, CI with Docker |
| **Key prefix** | Medium | Fast | High | Shared Redis, parallel test suites |

Default recommendation: **fakeredis for unit tests**, **testcontainers for integration tests**.

## Fixture Patterns

### Session-scoped real Redis client (DB isolation)

```python
# tests/conftest.py
import pytest
import redis
import os

@pytest.fixture(scope="session")
def redis_client():
    client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=15,  # dedicated test DB
        decode_responses=True,
    )
    client.flushdb()
    client.ping()
    yield client
    client.flushdb()
    client.close()
```

### Auto-cleanup between tests

```python
@pytest.fixture(autouse=True)
def clean_redis(redis_client):
    redis_client.flushdb()
    yield
```

Flush **before** each test, not only after, so crashes do not leave stale state.

### Service-under-test fixture

```python
@pytest.fixture
def cache_service(redis_client):
    from app.cache import CacheService
    return CacheService(client=redis_client)
```

### fakeredis for unit tests

```python
import pytest
import fakeredis

@pytest.fixture
def mock_redis():
    return fakeredis.FakeRedis(decode_responses=True)

@pytest.fixture
def cache_service(mock_redis):
    from app.cache import CacheService
    return CacheService(client=mock_redis)
```

Install: `uv add --dev fakeredis`

### Testcontainers for integration tests

```python
import pytest
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as container:
        yield container

@pytest.fixture(scope="session")
def redis_client(redis_container):
    import redis
    client = redis.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        decode_responses=True,
    )
    yield client
    client.close()
```

Install: `uv add --dev testcontainers[redis]`

## Key Isolation Strategies

### Separate DB index

Use `db=15` (or any unused index 1-15) for tests. Simple, fast, no key collisions. Limited to 16 DBs by default.

### Key prefix with UUID

Generate a unique per-session prefix for parallel runs on shared Redis:

```python
import uuid

@pytest.fixture(scope="session")
def test_prefix():
    return f"test:{uuid.uuid4().hex[:8]}:"
```

Wrap the client to auto-prefix all keys. See `references/isolation-patterns.md` for the full `PrefixedRedis` wrapper.

## Test Structure

Follow the same conventions as the `writing-unit-tests` skill:

- File naming: `test_*.py` under `tests/unit/` or `tests/integration/`
- Class grouping: `class TestCacheService:`
- Function naming: `def test_what_condition_expected():`
- Use `@pytest.mark.parametrize` when 3+ cases differ only by input/output

### Marking integration tests

```python
import pytest

pytestmark = pytest.mark.integration

class TestCacheIntegration:
    ...
```

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = ["integration: tests requiring a running Redis instance"]
```

Run selectively: `uv run pytest -m integration` or `uv run pytest -m "not integration"`

## Common Test Scenarios

### Basic CRUD

Test `set`, `get`, `delete`, and verify `None` for missing keys.

### TTL verification

```python
def test_set_with_ttl(self, cache_service, redis_client):
    cache_service.set("ttl_key", "value", ttl=60)
    ttl = redis_client.ttl("ttl_key")
    assert 55 <= ttl <= 60
```

### Concurrency (atomic increments)

Use `threading` for parallel `INCR` calls and assert the final count. See `examples/test_cache.py`.

### Pub/Sub

Subscribe in a background thread, publish messages, join with a timeout, assert received messages match. See `examples/test_pubsub.py`.

### Lua scripts

Register scripts via `redis_client.register_script()`, invoke with `keys` and `args`, and assert return values and side-effects. See `examples/test_lua_scripts.py`.

## CI/CD Integration

### GitHub Actions

Add a Redis service container:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

Set env vars `REDIS_HOST=localhost` and `REDIS_PORT=6379`; see `references/ci-config.md` for full GitHub Actions, GitLab CI, and Azure DevOps Pipelines examples.

## Dependencies

| Package | Purpose | Install |
|---|---|---|
| `redis` | Redis client | `uv add redis` |
| `fakeredis` | In-memory mock | `uv add --dev fakeredis` |
| `testcontainers[redis]` | Disposable containers | `uv add --dev testcontainers[redis]` |

## Additional Resources

### Reference Files

- **`references/isolation-patterns.md`** -- Key-prefix wrapper, DB-per-suite rotation, and parallel-safe patterns
- **`references/ci-config.md`** -- GitHub Actions, GitLab CI, and Azure DevOps Pipelines service container configs

### Example Files

Working test examples in `examples/`:

- **`examples/test_cache.py`** -- CRUD, TTL, increment, hash operations, concurrency
- **`examples/test_pubsub.py`** -- Channel subscribe, pattern subscribe
- **`examples/test_lua_scripts.py`** -- Rate limiter, atomic transfer scripts
- **`examples/conftest_fakeredis.py`** -- fakeredis-based conftest for unit tests
- **`examples/conftest_testcontainers.py`** -- testcontainers-based conftest for integration tests
