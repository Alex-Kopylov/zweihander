---
name: celery-expert
description: This skill should be used when the user asks to "configure Celery", "set up Celery with Redis", "write Celery tasks", "add background tasks with Celery", "celery beat schedule", "celery task retry", "celery performance tuning", "celery TDD", "test Celery tasks", "celery worker config", "celery monitoring", "celery security", or when code imports celery or the project uses a celeryconfig/celery.py module.
model: opus
---

# Celery Expert (Redis Broker)

## Overview

Expert guidance for building production-grade Celery distributed task queues with Redis as both broker and result backend. Covers task design, workflow orchestration (chains, groups, chords), scheduling with Celery Beat, performance tuning, monitoring, and security hardening.

**Core Principles:**

1. **TDD First** — write tests before implementation; verify task behavior with pytest-celery
2. **Performance Aware** — optimize throughput with chunking, pooling, and proper prefetch
3. **Reliability** — task retries, acknowledgment strategies, no task loss
4. **Security** — safe serialization (JSON only, never pickle), broker authentication
5. **Observable** — monitoring, metrics, tracing, alerting

**Pydantic models in tasks:** Manually serializing/deserializing Pydantic models (`.dict()`, `.model_dump()`, `**kwargs` unpacking) is ALWAYS an anti-pattern. Use the `celery-pydantic` package which handles serialization natively — it registers a custom serializer that lets you pass Pydantic models directly as task arguments.

## When to Apply

Activate when any of the following appear:

- `from celery import Celery` or `@app.task` / `@shared_task` in code
- `celeryconfig.py`, `celery.py`, or `beat_schedule` in project files
- User asks about background tasks, task queues, async processing, or distributed workers
- User mentions Flower, Celery Beat, task retries, or task routing

## TDD Workflow

Follow this 4-step cycle for every task:

1. **Write failing test** — use `task_always_eager=True` for unit tests
2. **Implement minimum to pass** — task with `bind=True`, proper error handling
3. **Refactor** — add time limits, observability, retry strategy
4. **Verify** — run full test suite with coverage

```python
@pytest.fixture
def celery_config():
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,
        'task_eager_propagates': True,
    }

class TestProcessOrder:
    def test_process_order_success(self, celery_app, celery_worker):
        from myapp.tasks import process_order
        result = process_order.delay(order_id=123)
        assert result.get(timeout=10) == {'order_id': 123, 'status': 'success'}

    def test_process_order_idempotent(self, celery_app, celery_worker):
        from myapp.tasks import process_order
        result1 = process_order.delay(order_id=123).get(timeout=10)
        result2 = process_order.delay(order_id=123).get(timeout=10)
        assert result1['status'] in ['success', 'already_processed']
        assert result2['status'] in ['success', 'already_processed']
```

See `examples/conftest_celery.py` for complete pytest fixture setup.

## Task Design Principles

Every task should follow these rules:

- **Idempotent** — safe to retry without side effects. Set values, don't increment them.
- **`bind=True`** — access `self.request.id`, `self.retry()`, and task metadata
- **JSON serializer** — never use pickle (remote code execution risk)
- **Time limits** — always set both `soft_time_limit` and `time_limit`
- **`acks_late=True`** for critical tasks — acknowledge after completion, not before
- **Small results** — store large data externally, return only references

```python
@app.task(
    bind=True,
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
    time_limit=300,
    soft_time_limit=240,
    rate_limit='100/m',
)
def process_order(self, order_id: int):
    ...
```

## Redis Broker Quick Config

```python
from celery import Celery

app = Celery('myapp')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,

    result_backend='redis://localhost:6379/1',
    result_expires=3600,

    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,
    task_soft_time_limit=240,

    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)
```

See `references/production-config.md` for complete production setup with TLS, beat, and deployment.

## Retry Strategy Summary

| Pattern | Use When | Config |
|---------|----------|--------|
| Manual retry | Custom backoff logic | `self.retry(exc=exc, countdown=2 ** self.request.retries)` |
| Auto-retry | Standard HTTP/network errors | `autoretry_for=(RequestException,), retry_backoff=True` |
| Auto-retry + jitter | High-concurrency retries | Add `retry_jitter=True, retry_backoff_max=600` |
| Reject (no retry) | Permanent failures, poison messages | `raise Reject(reason, requeue=False)` |

## Workflow Patterns

```python
from celery import chain, group, chord

# CHAIN: Sequential (A -> B -> C)
workflow = chain(fetch_data.s(url), process_item.s(), send_notification.s())

# GROUP: Parallel execution
job = group(fetch_data.s(url) for url in urls)

# CHORD: Map-Reduce (parallel + callback)
workflow = chord(group(process_item.s(item) for item in items))(aggregate_results.s())
```

## Pre-Implementation Checklist

**Before writing code:**
- [ ] Write failing test for task behavior
- [ ] Define idempotency strategy
- [ ] Choose queue routing for task priority
- [ ] Plan retry strategy and error handling

**Before deploying:**
- [ ] Time limits set (soft + hard)
- [ ] `acks_late=True` on critical tasks
- [ ] JSON serialization confirmed (not pickle)
- [ ] Redis broker authentication configured
- [ ] Result expiration set
- [ ] Monitoring active (Flower/Prometheus)
- [ ] Dead letter queue handling implemented

## Critical Reminders

**NEVER:** use pickle serialization, run without time limits, store large data in results, create non-idempotent tasks, run without broker auth, expose Flower without auth, manually serialize Pydantic models (use `celery-pydantic`)

**ALWAYS:** use JSON serialization, set time limits (soft + hard), make tasks idempotent, use `acks_late=True` for critical tasks, set result expiration, implement retry with backoff, monitor with Flower/Prometheus, log with correlation IDs

## Additional Resources

### Reference Files

- **`references/performance-patterns.md`** — Task chunking, prefetch tuning, result backend optimization, connection pooling, queue routing
- **`references/production-config.md`** — Complete Redis production config, beat scheduling, worker deployment, health checks
- **`references/security-standards.md`** — JSON serializer enforcement, Redis TLS/auth, input validation, Flower security
- **`references/common-mistakes.md`** — Anti-pattern table with fixes: pickle, idempotency, time limits, large results, pydantic serialization

### Example Files

Working code examples in `examples/`:

- **`examples/celery_app.py`** — App factory with Redis broker and recommended defaults
- **`examples/tasks.py`** — Task definitions: retry, chunking, idempotency patterns
- **`examples/celery_beat_schedule.py`** — Crontab and interval periodic task config
- **`examples/conftest_celery.py`** — Pytest fixtures for eager and integration testing
