# Redis Testing with pytest

## Overview

Redis unit and integration tests in Python with pytest: fixtures, isolation, fakeredis, testcontainers, pub/sub, Lua scripts, and concurrency.

## When to Load

Load this reference when any of the following appear in test code or user
intent:

- `import redis` or `from redis import ...` in test files or fixtures
- `fakeredis`, `testcontainers.redis`, or `RedisContainer` imports
- Fixtures that create a `redis.Redis` client
- Cache/session/queue services backed by Redis under test

## Backend Choice

Do not hand-roll Redis mocks. Use fakeredis and/or Testcontainers.

Mandatory read: `references/redis/fakeredis-vs-testcontainers.md` -- when to use
which, and how to avoid testing everything twice.

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

Backend-specific fixtures live in `references/redis/fakeredis.md` and
`references/redis/testcontainers.md`.

## Key Isolation Strategies

These apply when tests point at a Redis that is already running -- a CI service
container, or a local dev server. They are not an alternative to Testcontainers;
they are how to share one server safely once you have it. If nothing is running
yet, start a container instead of asking developers to install Redis.

### Separate DB index

Use `db=15` (or any unused index 1-15). Simple, fast, no key collisions, and
`FLUSHDB` clears only that index. Limited to 16 DBs by default, and `SELECT` is
unavailable on Redis Cluster.

### Key prefix with UUID

Generate a unique per-session prefix for parallel runs on shared Redis:

```python
import uuid

@pytest.fixture(scope="session")
def test_prefix():
    return f"test:{uuid.uuid4().hex[:8]}:"
```

Wrap the client to auto-prefix all keys. See
`references/redis/isolation-patterns.md` for the full `PrefixedRedis` wrapper.

Prefer a DB index. A wrapper only prefixes the commands it implements, so any
call the code under test makes through an unwrapped method escapes isolation
silently. Reach for prefixes only when parallel jobs must share one DB.

## Test Structure

Follow the same conventions as `tests-manager`:

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

Configure in `pyproject.toml` (see
[pytest markers](https://docs.pytest.org/en/stable/example/markers.html)):

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

Use `threading` for parallel `INCR` calls and assert the final count. See
`examples/redis/test_cache.py`.

### Pub/Sub

Subscribe in a background thread, publish messages, join with a timeout, assert
received messages match. See `examples/redis/test_pubsub.py`.

### Lua scripts

Register scripts via `redis_client.register_script()`, invoke with `keys` and
`args`, and assert return values and side-effects. See
`examples/redis/test_lua_scripts.py`.

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

Set env vars `REDIS_HOST=localhost` and `REDIS_PORT=6379`; see
`references/redis/ci-config.md` (GitHub Actions, GitLab CI) and
`references/redis/azure-devops-ci.md` (Azure DevOps Pipelines).

## Additional Resources

### Reference Files

- **`references/redis/fakeredis-vs-testcontainers.md`** -- Which backend to use when, and the shared contract-suite pattern
- **`references/redis/fakeredis.md`** -- Install, extras, fixtures, and the limitations that force a real-Redis test
- **`references/redis/testcontainers.md`** -- Install, fixtures, image pinning, Ryuk, and cost control
- **`references/redis/isolation-patterns.md`** -- Key-prefix wrapper, DB-per-suite rotation, and parallel-safe patterns
- **`references/redis/ci-config.md`** -- GitHub Actions and GitLab CI service container configs
- **`references/redis/azure-devops-ci.md`** -- Azure DevOps Pipelines service container configs

### Example Files

- **`examples/redis/test_cache.py`** -- CRUD, TTL, increment, hash operations, concurrency
- **`examples/redis/test_pubsub.py`** -- Channel subscribe, pattern subscribe
- **`examples/redis/test_lua_scripts.py`** -- Rate limiter, atomic transfer scripts
- **`examples/redis/conftest_fakeredis.py`** -- fakeredis-based conftest for unit tests
- **`examples/redis/conftest_testcontainers.py`** -- testcontainers-based conftest for integration tests

### External Documentation

- [redis-py](https://redis-py.readthedocs.io/en/stable/) -- official Python client
- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) and [markers](https://docs.pytest.org/en/stable/example/markers.html)
- [Redis command reference](https://redis.io/docs/latest/commands/)

Backend library docs live in the per-library references above.
