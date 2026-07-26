# Testing Celery with pytest

## When to Load

Load this reference when tests cover Celery tasks, retries, routing, canvas
workflows, Beat schedules, worker execution, broker transport, or result
backends.

## Choose the Smallest Useful Test

| Target | Test level | Default approach |
|---|---|---|
| Business logic called by a task | Unit | Test the plain function or service without Celery |
| Thin task adapter, argument handling, or retry branch | Unit | Call the task directly; mock collaborators and `Task.retry` |
| Serialization, headers, routing, canvas, or worker behavior | Integration | Use `celery.contrib.pytest` with a live embedded worker |
| Broker/backend compatibility or production topology | Smoke | Use Docker-based `pytest-celery` |

Keep task functions thin so most behavior remains fast to test without a broker
or worker.

## Eager Mode Boundary

Do not use `task_always_eager` as the default unit-test strategy. Eager mode
emulates worker execution and does not prove broker transport, serialization,
worker lifecycle, or result-backend behavior.

Use eager mode only when the eager configuration itself is the subject of the
test. Do not combine it with `celery_worker` and claim worker coverage.

## Unit Tests

- Test domain behavior outside the task first.
- Call the task directly for adapter behavior; do not call `.delay()`.
- Patch dependencies where the task module looks them up.
- Mock `task.retry` and make it raise `celery.exceptions.Retry` when testing a
  retry branch.
- Assert task arguments, collaborator calls, retry options, and returned values.
- Keep serialization and delivery assertions for integration tests.

See `examples/celery/test_tasks.py` for task-adapter examples.

## Live-Worker Integration Tests

Use `celery.contrib.pytest` when a test must cross the task-message-worker
boundary. Install the plugin with:

```shell
uv add --dev "celery[pytest]"
```

Register `celery.contrib.pytest`, provide a `celery_config` fixture, and request
both `celery_app` and `celery_worker` in the test. After defining a task on
`celery_app`, call `celery_worker.reload()` before dispatching it.

Always use a timeout with `AsyncResult.get()` so a failed worker cannot hang the
suite. See `examples/celery/conftest.py` for a focused setup.

## Production-Like Smoke Tests

Use `pytest-celery` only when Docker-based workers, brokers, and result backends
must resemble production. Its fixtures and configuration are separate from
`celery.contrib.pytest`; do not mix both APIs in one test setup.

Keep this layer small. Cover representative delivery, readiness, and
broker/backend compatibility paths rather than repeating unit cases.

## Isolation

- Give Redis brokers and result backends dedicated test DBs or containers.
- Use unique queues when suites can run in parallel.
- Purge only test-owned queues and result data.
- Stop workers through fixture teardown; do not leave background processes.
- Load `references/redis-testing.md` when Redis lifecycle or key isolation is
  part of the test.

## Coverage Checklist

- Task adapter delegates the expected arguments.
- Retryable failures call `retry` with the intended exception and delay policy.
- Permanent failures do not requeue indefinitely.
- Idempotent tasks tolerate duplicate delivery.
- Worker-level tests cover serialization or routing only when those boundaries
  matter.
- Canvas workflows assert final behavior for representative chain, group, or
  chord paths.
- Beat tests validate schedule configuration without sleeping for real time.

## Example Files

- **`examples/celery/conftest.py`** — embedded-worker pytest plugin and broker/backend configuration
- **`examples/celery/test_tasks.py`** — task-adapter unit tests and a live-worker integration test
