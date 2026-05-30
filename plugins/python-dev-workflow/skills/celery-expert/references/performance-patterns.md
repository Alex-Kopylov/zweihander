# Performance Patterns

## Task Chunking

Dispatching thousands of individual tasks creates broker overhead (message routing, serialization, acknowledgment per message). Batch items into chunks instead.

```python
# Bad — 10,000 items = 10,000 tasks
for item_id in item_ids:
    process_item.delay(item_id)

# Good — 100 tasks of 100 items each
@app.task
def process_batch(item_ids: list[int]):
    results = []
    for chunk in chunks(item_ids, size=100):
        items = fetch_items_bulk(chunk)  # single DB query per chunk
        results.extend([process(item) for item in items])
    return results

for chunk in chunks(item_ids, size=100):
    process_batch.delay(chunk)
```

Rule of thumb: aim for ~100 items per task. Adjust based on per-item processing time — if each item takes 1s, use smaller chunks to avoid hitting time limits.

## Prefetch Tuning

Prefetch controls how many broker messages a worker reserves; tune it by task type:

| Task Type | `worker_prefetch_multiplier` | Pool | Concurrency | Why |
|-----------|------------------------------|------|-------------|-----|
| CPU-bound (compute, ML) | 4 | prefork | CPU count | Keep workers busy, minimize idle time |
| I/O-bound (API calls, DB) | 1 | gevent | 100-500 | Don't reserve messages that could go to idle greenlets |
| Long-running (>60s) | 1 | prefork | low (2-4) | Prevent starvation of other tasks |

```python
# CPU-bound
app.conf.worker_prefetch_multiplier = 4
# celery -A app worker --concurrency=4

# I/O-bound
app.conf.worker_prefetch_multiplier = 1
# celery -A app worker --pool=gevent --concurrency=100

# Long tasks — also enable acks_late so tasks return to queue on crash
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
```

## Connection Pooling

Per-task DB or Redis connections are expensive. Initialize module-level pools shared by tasks in each worker process.

```python
from sqlalchemy import create_engine
from redis import ConnectionPool, Redis

# Initialize once at module level — shared across all tasks in this worker
db_engine = create_engine(
    'postgresql://user:pass@localhost/db',
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
redis_pool = ConnectionPool(host='localhost', port=6379, max_connections=50)

@app.task
def query_database(query: str):
    with db_engine.connect() as conn:
        return conn.execute(query).fetchall()

@app.task
def cache_result(key: str, value: str):
    client = Redis(connection_pool=redis_pool)
    client.set(key, value)
```

When using `worker_max_tasks_per_child` (recommended to prevent memory leaks), pools are recreated when the worker child process restarts — this is expected behavior.

## Task Routing

Route tasks to dedicated queues so that slow bulk tasks don't block time-sensitive operations.

```python
from kombu import Queue, Exchange

app.conf.task_queues = (
    Queue('critical', Exchange('critical'), routing_key='critical'),
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('bulk', Exchange('bulk'), routing_key='bulk'),
)

app.conf.task_routes = {
    'tasks.critical_payment': {'queue': 'critical'},
    'tasks.send_email': {'queue': 'default'},
    'tasks.generate_report': {'queue': 'bulk'},
}
```

Run dedicated workers per queue with appropriate concurrency:

```bash
celery -A app worker -Q critical --concurrency=4
celery -A app worker -Q default --concurrency=8
celery -A app worker -Q bulk --concurrency=2
```

## Monitoring Integration

### Flower

Real-time web UI for monitoring workers, tasks, and queues:

```bash
celery -A app flower --port=5555 --basic_auth=admin:password
```

Never expose Flower without authentication in production.

### Prometheus Metrics

Export task metrics for alerting on queue depth, latency, and failure rates:

```python
from prometheus_client import Counter, Histogram

task_counter = Counter('celery_tasks_total', 'Total tasks', ['task_name', 'status'])
task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
```

### Correlation IDs

Track tasks across systems by logging the task ID:

```python
@app.task(bind=True)
def process_order(self, order_id: int):
    logger.info(
        "Processing order",
        extra={'task_id': self.request.id, 'order_id': order_id},
    )
```
