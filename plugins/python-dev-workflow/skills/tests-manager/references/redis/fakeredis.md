# fakeredis

In-process Redis implementation for fast unit tests. No server, no Docker, no
sockets.

- [docs](https://fakeredis.readthedocs.io/en/latest/) --
  [supported commands](https://fakeredis.readthedocs.io/en/latest/supported-commands/)
  -- [source](https://github.com/cunla/fakeredis-py)
- Backend choice: `references/redis/fakeredis-vs-testcontainers.md`

## Install

```shell
uv add --dev fakeredis
```

Optional features ship as extras and are simply absent without them:

| Extra | Pulls in | Enables |
|---|---|---|
| `lua` | `lupa` | `EVAL` / `EVALSHA` scripting |
| `json` | `jsonpath-ng` | `JSON.*` commands |
| `bf` | `pyprobables` | Bloom filters |
| `cf` | `pyprobables` | Cuckoo filters |
| `probabilistic` | `pyprobables` | All of the above: Bloom, Cuckoo, Count-Min, Top-K |
| `valkey` | `valkey` | valkey-py client compatibility |
| `vectorset` | `numpy`, `jsonpath-ng` | Vector set commands; Python 3.11+ only |

`bf`, `cf`, and `probabilistic` all resolve to the same `pyprobables`
dependency, so `probabilistic` alone covers every filter type.

Combine what the code under test actually calls:

```shell
uv add --dev "fakeredis[lua,json]"
```

Without the matching extra the test fails on an unknown command rather than on
the behaviour it was written to check.

## Fixtures

### Unit test client

```python
import fakeredis
import pytest


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def cache_service(fake_redis):
    from app.cache import CacheService

    return CacheService(client=fake_redis)
```

No flush fixture is needed when the client is function-scoped: each test builds
a fresh in-memory store.

### Async client

`FakeAsyncRedis` mirrors the async redis-py API:

```python
@pytest.fixture
async def fake_redis():
    return fakeredis.FakeAsyncRedis(decode_responses=True)
```

### Shared state across clients

Pass one `FakeServer` when several clients must see the same keyspace, such as
a producer and a consumer in the same test:

```python
@pytest.fixture
def fake_server():
    return fakeredis.FakeServer()


@pytest.fixture
def producer(fake_server):
    return fakeredis.FakeRedis(server=fake_server, decode_responses=True)


@pytest.fixture
def consumer(fake_server):
    return fakeredis.FakeRedis(server=fake_server, decode_responses=True)
```

### Simulating a dead server

Toggling `connected` makes commands raise connection errors, which is the one
resilience path fakeredis can exercise:

```python
def test_cache_falls_back_when_redis_is_down(fake_server, cache_service):
    fake_server.connected = False
    assert cache_service.get("key") is None
```

For real timeouts, retries, and pool exhaustion, use Testcontainers.

## Limitations

Documented divergences and structural gaps. Validate affected behavior against
real Redis:

| Area | fakeredis behaviour |
|---|---|
| [`EVAL`](https://redis.io/docs/latest/commands/eval/) / `EVALSHA` | Requires the `lua` extra; absent without it |
| `JSON.*`, Bloom / Cuckoo / Top-K | Require the `json` / `probabilistic` extras |
| [HyperLogLog](https://redis.io/docs/latest/commands/pfcount/) | Backed by sets, so `TYPE` and cardinality results differ |
| [`INCRBYFLOAT`](https://redis.io/docs/latest/commands/incrbyfloat/) / `HINCRBYFLOAT` | Lower precision than the C `long double` Redis uses |
| Blocking pops ([`BLPOP`](https://redis.io/docs/latest/commands/blpop/)) | Wake-up ordering across blocked clients is not guaranteed |
| [`SCAN`](https://redis.io/docs/latest/commands/scan/) family | May miss items when the keyspace mutates during iteration |
| [`DUMP`](https://redis.io/docs/latest/commands/dump/) / `RESTORE` | Python `pickle`, not RDB; payloads are not interchangeable |
| [`CLIENT PAUSE`](https://redis.io/docs/latest/commands/client-pause/), client addresses | No-op; every connection reports `127.0.0.1:0` |
| Connection failures | In-process, no sockets: timeouts, retries, reconnects and pool exhaustion never fire |
| Server-level features ([eviction](https://redis.io/docs/latest/develop/reference/eviction/), [keyspace notifications](https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/), replication, cluster, persistence) | Partially emulated or absent; check [supported commands](https://fakeredis.readthedocs.io/en/latest/supported-commands/) before relying on one |
| Server version | Emulated, and may not match the deployed image |

Also emulates Valkey, DragonflyDB, and KeyDB, with the same caveat: the
emulation is not the product.
