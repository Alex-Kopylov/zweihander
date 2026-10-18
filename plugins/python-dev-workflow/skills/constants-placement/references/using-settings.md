# Reading Settings

Read inside the function that needs the value, so importing never depends on
the environment:

```python
def charge(amount_cents: int) -> None:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.stripe_api_key.get_secret_value()}"}
    httpx.post(URL, headers=headers, timeout=settings.request_timeout_seconds)
```

A module that already acted on the value at import keeps doing so:

```python
logging.basicConfig(level=get_settings().log_level)
```

In FastAPI, inject it: `settings: Annotated[Settings, Depends(get_settings)]`.

## `tests/conftest.py`

```python
@pytest.fixture(autouse=True)
def settings_env(monkeypatch):
    monkeypatch.setenv("APP_STRIPE_API_KEY", "sk_test")
    monkeypatch.setenv("APP_DB__PASSWORD", "test")
    get_settings.cache_clear()  # each test gets settings built from its own environment
    yield
    get_settings.cache_clear()
```

In FastAPI tests, `app.dependency_overrides[get_settings]` replaces the whole
object instead.
