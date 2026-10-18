# The Settings Class

`BaseSettings` comes from the separate `pydantic-settings` package, not
`pydantic`.

```python
from functools import cache
from typing import Literal

from pydantic import Field, PositiveInt, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",  # only for a new class; an existing one keeps its variable names
        env_file=".env",
        extra="ignore",  # .env may hold variables other tools read
    )

    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    request_timeout_seconds: float = Field(30.0, gt=0)  # the old hardcoded value is the default
    worker_count: PositiveInt = 4

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


@cache
def get_settings() -> Settings:
    return Settings()
```

- Precedence: environment variables, then `.env`, then field defaults.
- `.env.example` is committed next to the ignored `.env` and lists every
  variable: config with its default, secrets empty.

```dotenv
APP_ENVIRONMENT=dev
APP_LOG_LEVEL=INFO
APP_REQUEST_TIMEOUT_SECONDS=30
APP_WORKER_COUNT=4
```
