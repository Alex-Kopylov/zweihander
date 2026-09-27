# Common Mistakes

## Anti-Pattern Table

| Mistake | Why It's Dangerous | Fix |
|---------|-------------------|-----|
| Pickle serialization | Allows remote code execution via crafted messages | `task_serializer='json'`, `accept_content=['json']` |
| Non-idempotent tasks | Retries cause side effects (double charges, duplicate emails) | Set values, don't increment; check state before acting |
| Missing time limits | Tasks hang forever, workers become unresponsive | Always set both `soft_time_limit` and `time_limit` |
| Large results in Redis | Redis OOM, result backend bloat | `ignore_result=True` for fire-and-forget; store large data externally |
| New connection per task | Connection overhead kills throughput | Module-level connection pools (SQLAlchemy, redis-py) |
| Manual pydantic serialization | Brittle, error-prone, loses validation | Use `celery-pydantic` package for native support |
| No broker authentication | Anyone on the network can inject tasks | Always set Redis password; use TLS in production |
| Flower without auth | Exposes task data and worker controls publicly | `--basic_auth` or deploy behind authenticated reverse proxy |

## Detailed Examples

### Pickle Serialization

```python
# DON'T — allows arbitrary code execution
app.conf.task_serializer = 'pickle'

# DO — JSON is safe
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
```

### Non-Idempotent Tasks

```python
# DON'T — retries increment multiple times
@app.task
def increment_counter(user_id: int):
    user = get_user(user_id)
    user.counter += 1  # retry = double increment
    user.save()

# DO — safe to retry
@app.task
def set_counter(user_id: int, value: int):
    user = get_user(user_id)
    user.counter = value  # retry = same result
    user.save()
```

### Missing Time Limits

```python
# DON'T — hangs forever if external service is down
@app.task
def slow_task():
    external_api_call()

# DO — fails cleanly after timeout
@app.task(time_limit=30, soft_time_limit=25)
def safe_task():
    external_api_call()
```

Handle `SoftTimeLimitExceeded` for graceful cleanup:

```python
from celery.exceptions import SoftTimeLimitExceeded

@app.task(bind=True, time_limit=300, soft_time_limit=240)
def long_task(self, job_id: int):
    try:
        process_job(job_id)
    except SoftTimeLimitExceeded:
        cleanup_partial_work(job_id)
        raise
```

### Large Results in Redis

```python
# DON'T — stores entire file content in Redis
@app.task
def process_file(file_id: int):
    return read_large_file(file_id)  # could be megabytes

# DO — store externally, return reference
@app.task
def process_file(file_id: int):
    data = process(read_large_file(file_id))
    result_key = save_to_s3(data)
    return {'result_key': result_key}
```

### Manual Pydantic Serialization

```python
# DON'T — manual conversion is brittle and loses validation context
@app.task
def process_order(order_data: dict):
    validated = OrderData(**order_data)
    return process(validated.dict())  # anti-pattern

# DO — use celery-pydantic for native Pydantic support
# Install: uv add celery-pydantic
# celery-pydantic handles serialization/deserialization automatically
```

### Blocking I/O in Gevent/Eventlet Workers

```python
# DON'T — blocking calls defeat the purpose of async pools
import time

@app.task
def bad_gevent_task():
    time.sleep(10)  # blocks the greenlet AND the event loop

# DO — use gevent-compatible I/O
import gevent

@app.task
def good_gevent_task():
    gevent.sleep(10)  # yields control to other greenlets
```

When using `--pool=gevent` or `--pool=eventlet`, ensure all I/O libraries are monkey-patched or natively async. Common offenders: `time.sleep()`, synchronous HTTP clients, blocking DB drivers.
