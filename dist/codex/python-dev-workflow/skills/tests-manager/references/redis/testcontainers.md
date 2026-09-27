# Testcontainers Redis

Disposable real Redis in Docker, started and torn down by the test session.

- [Testcontainers for Python](https://testcontainers-python.readthedocs.io/en/latest/)
  -- [Redis module](https://testcontainers-python.readthedocs.io/en/latest/modules/redis/README.html)
  -- [source](https://github.com/testcontainers/testcontainers-python)
- Backend choice: `references/redis/fakeredis-vs-testcontainers.md`

## Install

```shell
uv add --dev testcontainers[redis]
```

Requires a reachable Docker daemon. In Docker-in-Docker CI, mount
`/var/run/docker.sock` or set `DOCKER_HOST`.

## Fixtures

Keep the container session-scoped. A container per test costs seconds per test.

```python
import pytest
import redis
from testcontainers.redis import RedisContainer

REDIS_IMAGE = "redis:7-alpine"


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer(REDIS_IMAGE) as container:
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

Flush before each test, not only after, so a crashed test cannot leak state.

`RedisContainer` also exposes `get_client()`, which builds the client for you.
Constructing it explicitly is worth the two extra lines when the test needs
`decode_responses` or other client kwargs.

`RedisContainer` defaults to `redis:latest`. Always pin, and pin to the image
actually deployed -- an unpinned test server silently drifts away from
production and defeats the reason for using a real one.

## Keeping It Cheap

A real server is the slow half of the suite. Contain the cost:

- Session-scope the container; flush between tests instead of restarting.
- Gate it behind `@pytest.mark.integration` so `-m "not integration"` never
  starts Docker.
- Test only what actually needs real Redis. See the divergence table in
  `references/redis/fakeredis.md`.

## When A CI Service Container Is Better

If CI already provides Redis through a service block -- as in
`references/redis/ci-config.md` and `references/redis/azure-devops-ci.md` --
that server is just as real as a Testcontainers one and is already running.
Connecting to it and isolating by DB index costs nothing, while Testcontainers
would pull and boot a second server inside the job.

Prefer Testcontainers when:

- The suite must run identically on a laptop and in CI with no external setup.
- Tests need a version, module, or config the CI service block does not offer.
- Parallel jobs would otherwise contend for one shared server.

Prefer the CI service container when Redis is already provisioned and the tests
only need a clean keyspace. See `references/redis/isolation-patterns.md`.

## Ryuk

Testcontainers starts a Ryuk sidecar to reap containers if the session dies.
Relevant environment variables:

| Variable | Purpose |
|---|---|
| `TESTCONTAINERS_RYUK_DISABLED` | Disable the reaper entirely |
| `TESTCONTAINERS_RYUK_PRIVILEGED` | Run Ryuk privileged, needed in some DinD setups |
| `TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE` | Socket path Ryuk should use |
| `TESTCONTAINERS_HOST_OVERRIDE` | Manual gateway IP when autodetection fails |
| `DOCKER_AUTH_CONFIG` | Registry auth for private images |

Disabling Ryuk leaks containers when a run is killed. Prefer fixing the socket
or privilege setting over disabling it.
