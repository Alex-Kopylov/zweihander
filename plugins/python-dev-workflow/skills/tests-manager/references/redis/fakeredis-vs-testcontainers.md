# fakeredis vs Testcontainers Redis

## Overview

How to split Redis coverage between an in-memory fake and a real server
without maintaining the same suite twice.

Backend detail lives in the per-library references:

- `references/redis/fakeredis.md` -- install, extras, fixtures, limitations
- `references/redis/testcontainers.md` -- install, fixtures, image pinning, cost

## What To Use When

Default to fakeredis. Escalate to a real server when the behaviour under test
is something a fake cannot have.

| What the test exercises | Backend |
|---|---|
| Application logic over a cache, session, or queue API | fakeredis |
| Key naming, serialization, branches, error handling | fakeredis |
| Anything in an environment without Docker | fakeredis |
| Lua scripts, `JSON.*`, Bloom filters, HyperLogLog, float precision | Testcontainers |
| Blocking pops, `SCAN` over a mutating keyspace, `DUMP`/`RESTORE` | Testcontainers |
| Connection loss, timeouts, retries, pool exhaustion | Testcontainers |
| Eviction, keyspace notifications, replication, cluster | Testcontainers |
| Distributed locks, `WATCH` races, real concurrency | Testcontainers |
| Anything, when CI already runs Redis as a service | that server, isolated by DB index |

The full catalogue of what fakeredis gets wrong is the limitations table in
`references/redis/fakeredis.md`. When a behaviour is not on it and not
server-level, fakeredis is enough.

## Default Split

| Layer | Backend | What it proves |
|---|---|---|
| Unit / component | fakeredis | Application logic: key naming, serialization, branches, error handling |
| Integration / contract | Testcontainers | Redis semantics: real commands, real connections, real concurrency |

```text
tests/
├── unit/
│   └── test_cache_service.py        # fakeredis
├── integration/
│   └── test_redis_integration.py    # Testcontainers
└── conftest.py
```

Mark the slow side so the fast suite runs on its own
([pytest markers](https://docs.pytest.org/en/stable/example/markers.html)):

```python
@pytest.mark.integration
def test_distributed_lock(real_redis): ...
```

Run with `uv run pytest -m "not integration"` for the fast loop.

## The Duplication Trap

Running every test against both backends doubles runtime and maintenance
while proving almost nothing: logic that passes on fakeredis fails on real
Redis only when it touches a divergence.

Scope instead:

- Application logic -- fakeredis only, tested exhaustively.
- Divergent behaviour -- targeted Testcontainers coverage.
- Shared assumptions (serialization, expiry, basic commands) -- a focused
  contract suite against both.

Rule of thumb: most tests use fakeredis; every behaviour that depends on actual
Redis semantics gets targeted Testcontainers coverage.

## Contract Suite Against Both Backends

Use a parametrized fixture only for assumptions shared by both backends --
serialization, expiry, basic commands -- never for the whole suite.

```python
# tests/contract/conftest.py
import pytest

REDIS_IMAGE = "redis:7-alpine"


@pytest.fixture(scope="session")
def redis_container():
    from testcontainers.redis import RedisContainer

    with RedisContainer(REDIS_IMAGE) as container:
        yield container


@pytest.fixture(
    params=[
        pytest.param("fake", id="fakeredis"),
        pytest.param("real", id="real", marks=pytest.mark.integration),
    ]
)
def redis_client(request):
    if request.param == "fake":
        import fakeredis

        client = fakeredis.FakeRedis(decode_responses=True)
    else:
        import redis

        container = request.getfixturevalue("redis_container")
        client = redis.Redis(
            host=container.get_container_host_ip(),
            port=container.get_exposed_port(6379),
            decode_responses=True,
        )

    client.flushall()
    yield client
    client.close()
```

Marking the `real` param with `integration` means `-m "not integration"`
deselects it and the container never starts, so the fast suite stays
Docker-free. See
[marks with parametrized fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#using-marks-with-parametrized-fixtures).

## Pitfalls

- Yield a client, not the module or the container. `return fakeredis` hands
  tests the module; `yield container` hands them an object with no `.set()`.
- Never mix `return` and `yield` in one fixture. Python turns the whole function
  into a generator, so the `return` branch yields nothing and pytest fails with
  "did not yield a value".
- Keep the container fixture session-scoped. A `RedisContainer` opened inside a
  function-scoped fixture starts and stops one container per test.
- Flush before yielding, not only after, so a crashed test cannot leak state
  into the next one.

## Related

- `references/redis-testing.md` -- fixtures, isolation, CI, common scenarios
- `references/redis/isolation-patterns.md` -- key prefixes and DB rotation
- `examples/redis/conftest_fakeredis.py`, `examples/redis/conftest_testcontainers.py`
