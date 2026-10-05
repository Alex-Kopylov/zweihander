# pydantic-settings Patterns

The `BaseSettings` class lives in the `pydantic-settings` package, separate
from `pydantic`. Add it through the project's package manager.

## The settings module

```python
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Config: the old hardcoded value is the default. Env: REQUEST_TIMEOUT_SECONDS.
    request_timeout_seconds: float = 30.0

    # Secret: no default, the value lives only in .env. Env: STRIPE_API_KEY.
    stripe_api_key: SecretStr

    # Existing variable whose name the field does not produce: keep the name.
    smtp_user: str = Field("reports@example.com", validation_alias="MAIL_USER")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- `extra="ignore"`: `.env` may hold variables other tools read.
- Environment variables override `.env`; matching is case-insensitive.
- `validation_alias` ignores `env_prefix`, so it pins an exact existing name.
- `SecretStr` prints as `**********` in logs, reprs and tracebacks.

## Reading values

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

## Grouping new variables

Only for variables nothing reads yet, since nesting changes the variable
names:

```python
from pydantic import BaseModel


class QueueSettings(BaseModel):  # BaseModel, not BaseSettings
    host: str = "localhost"
    port: int = 5672


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_nested_delimiter="__")

    queue: QueueSettings = QueueSettings()  # QUEUE__HOST, QUEUE__PORT
```

## Tests

```python
@pytest.fixture(autouse=True)
def fresh_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_short_timeout(monkeypatch):
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "1")
    ...
```

## `.env.example`

Committed next to the ignored `.env`. Config with its default, secrets
empty:

```dotenv
REQUEST_TIMEOUT_SECONDS=30
STRIPE_API_KEY=
```
