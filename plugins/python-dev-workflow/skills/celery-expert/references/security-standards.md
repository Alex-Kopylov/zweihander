# Security Standards

## Serialization: JSON Only

Pickle serialization allows arbitrary code execution. An attacker who can inject messages into the broker can run any Python code on your workers.

```python
# DANGEROUS — never use pickle
app.conf.task_serializer = 'pickle'  # remote code execution risk!

# SECURE — JSON only
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],  # reject anything that isn't JSON
)
```

This means task arguments and return values must be JSON-serializable (strings, numbers, lists, dicts, booleans, None). For Pydantic models, use the `celery-pydantic` package — it registers a custom serializer that handles Pydantic models natively. Never manually convert models with `.dict()` or `.model_dump()`.

## Redis Broker Authentication & TLS

### Password Authentication

```python
# Basic auth
app.conf.broker_url = 'redis://:your-strong-password@redis-host:6379/0'
```

### TLS Encryption

```python
# TLS connection (use rediss:// — double s)
app.conf.broker_url = 'rediss://:password@redis-host:6380/0'
app.conf.broker_use_ssl = {
    'ssl_cert_reqs': 'required',
    'ssl_ca_certs': '/path/to/ca.pem',
    'ssl_certfile': '/path/to/client.pem',
    'ssl_keyfile': '/path/to/client.key',
}

# Apply same TLS config to result backend
app.conf.redis_backend_use_ssl = app.conf.broker_use_ssl
```

### Environment Variables for Secrets

Never hardcode credentials in source code:

```python
import os

app.conf.broker_url = os.environ['CELERY_BROKER_URL']
app.conf.result_backend = os.environ['CELERY_RESULT_BACKEND']
```

## Input Validation

Validate all task arguments at the boundary. Use `celery-pydantic` for native Pydantic support, or validate manually for simple cases:

```python
@app.task(bind=True)
def process_order(self, order_id: int, amount: float):
    if not isinstance(order_id, int) or order_id <= 0:
        raise ValueError(f"Invalid order_id: {order_id}")
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError(f"Invalid amount: {amount}")
    # proceed with validated inputs
```

## Rate Limiting

Protect downstream services from being overwhelmed by task bursts:

```python
@app.task(rate_limit='100/m')  # max 100 executions per minute per worker
def call_external_api(url: str):
    ...

@app.task(rate_limit='10/s')  # 10 per second per worker
def send_notification(user_id: int):
    ...
```

## Flower Security

Flower (the Celery monitoring web UI) must never be exposed without authentication:

```bash
# Basic auth
celery -A app flower --basic_auth=admin:strong-password

# Behind reverse proxy with TLS
celery -A app flower --address=127.0.0.1 --port=5555
# Then proxy via nginx with TLS termination and auth
```

For production, run Flower behind a reverse proxy (nginx/traefik) with:
- TLS termination
- Authentication (OAuth2, basic auth, or your org's SSO)
- IP allowlisting if possible
