# Secrets in Settings

```python
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "app"
    user: str = "app"
    password: SecretStr  # no default: a missing value fails at startup, not in production

    @property  # a property, not computed_field: computed fields serialize, and this one holds the password
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_nested_delimiter="__", env_file=".env")

    stripe_api_key: SecretStr  # APP_STRIPE_API_KEY
    db: DatabaseSettings  # APP_DB__PASSWORD
```

- `SecretStr` prints as `**********` in reprs, logs and `model_dump()`;
  call `.get_secret_value()` only at the point of use.
- The value goes to `.env`; `.env.example` lists the variable with an empty
  value (`APP_STRIPE_API_KEY=`).
- Secret files from Docker or Kubernetes: add `secrets_dir="/run/secrets"`
  to `model_config`; each file is named like the variable. A missing
  directory only warns, so keep it out of local-only setups.
