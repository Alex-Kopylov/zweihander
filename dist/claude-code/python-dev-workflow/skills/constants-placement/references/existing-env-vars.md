# Variables a Deployment Already Sets

A renamed variable is silently ignored and the default wins, so a name the
code already reads (`os.getenv("SMTP_USER")`) survives the move unchanged.

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):  # a nested group is a BaseModel, not a BaseSettings
    host: str = "localhost"
    port: int = 5432


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_nested_delimiter="__")

    # validation_alias ignores env_prefix: this field reads SMTP_USER, not APP_SMTP_USER.
    smtp_user: str = Field("reports@example.com", validation_alias="SMTP_USER")

    # Nesting renames variables to APP_DB__HOST, APP_DB__PORT: group only variables nothing reads yet.
    db: DatabaseSettings = DatabaseSettings()
```

- Field name plus `env_prefix` must produce the existing name; when it
  cannot, `validation_alias` pins it exactly.
- Matching is case-insensitive, so `smtp_user` reads `SMTP_USER` without an
  alias when there is no prefix.
