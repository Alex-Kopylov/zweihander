---
name: writing-unit-tests
description: Use when writing, adding, or modifying unit tests for a Python project using pytest, unittest.mock, and conftest hierarchy. Covers file naming, test structure, mocking patterns (DB/cache clients, external API clients), assertions, and coverage goals.
---

# Writing Unit Tests

## Overview

Unit tests for a Python project using pytest. Follow the conventions below for file naming, test structure, mock patterns, and assertions.

## File Naming & Location

- Always `test_*.py` — never `.spec.*` or `*_test.py`
- Mirror the `src/` package structure under `tests/unit/`:
  - `tests/unit/api/` — API layer
  - `tests/unit/services/` — service layer
  - `tests/unit/models/` — data models
- Shared data files: `tests/fixtures/`
- Shared fixture definitions: `tests/conftest.py` (root) and `tests/unit/conftest.py` (unit scope)

## Test Naming

- Group tests with `class TestMethodName:` (mirrors the function or class under test)
- Use nested classes for scenario grouping when needed
- Test functions: `def test_what_condition_expected():` — snake_case, descriptive, no "should"
- Always `def test_...()` — never wrap in a plain function without the `test_` prefix

## Mock Patterns

Use `unittest.mock` as the primary mocking library. `pytest-mock` (`mocker` fixture) is acceptable as an alternative.

### Core mock primitives

```python
from unittest.mock import patch, MagicMock, Mock, create_autospec

# Patch a name in the module under test
with patch("src.services.payments.get_db_client") as mock_client:
    mock_client.return_value = MagicMock()
    result = payments.process(...)

# Decorator form (preferred for test methods)
@patch("src.services.payments.get_db_client")
def test_process_success(mock_client):
    mock_client.return_value = MagicMock()
    ...

# mocker fixture (pytest-mock)
def test_process_success(mocker):
    mock_client = mocker.patch("src.services.payments.get_db_client")
    mock_client.return_value = MagicMock()
    ...
```

### DB / cache client mocking

Mock at the client-factory level — never mock individual SQL queries or cache commands directly.

```python
@patch("src.repositories.users.get_db_client")
def test_get_user_found(mock_get_client):
    mock_db = MagicMock()
    mock_get_client.return_value = mock_db
    mock_db.execute.return_value = [{"id": "u-1", "name": "Alice"}]

    result = users.get_user(user_id="u-1")

    assert result == {"id": "u-1", "name": "Alice"}
    mock_db.execute.assert_called_once_with(...)
```

### External API client mocking

```python
@patch("src.integrations.stripe.get_api_client")
def test_charge_success(mock_get_client):
    mock_stripe = MagicMock()
    mock_get_client.return_value = mock_stripe
    mock_stripe.charges.create.return_value = {"id": "ch_1", "status": "succeeded"}

    result = stripe.charge(amount=1000, currency="usd")

    assert result["status"] == "succeeded"
    mock_stripe.charges.create.assert_called_once_with(amount=1000, currency="usd")
```

### Partial mocking with patch.object and side_effect

```python
# Mock only one method on a real object
with patch.object(MyService, "external_call", return_value={"ok": True}):
    result = MyService().run()

# Selectively raise for some inputs
def selective_fetch(user_id: str) -> dict:
    if user_id == "bad":
        raise ValueError("not found")
    return {"id": user_id}

mock_fetch.side_effect = selective_fetch
```

### Async testing

Use `@pytest.mark.asyncio` for async functions. Use `AsyncClient` for FastAPI route testing.

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_fetch_user_async():
    result = await users.fetch_async(user_id="u-1")
    assert result == {"id": "u-1", "name": "Alice"}

# FastAPI route
@pytest.mark.asyncio
async def test_get_user_route(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users/u-1")
    assert response.status_code == 200
    assert response.json()["id"] == "u-1"
```

### Standard Python imports — no path aliases

```python
# Correct
from src.services.payments import process_payment
from tests.fixtures.users import create_user

# Wrong — no @/ or root/ aliases
```

## Setup / Teardown

Fixtures are function-scoped by default — each test gets a fresh mock. No explicit reset is needed.

Use `yield` for teardown when a fixture acquires resources:

```python
# tests/unit/conftest.py

import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture()
def mock_db_client():
    with patch("src.repositories.base.get_db_client") as mock_get:
        mock_db = MagicMock()
        mock_get.return_value = mock_db
        yield mock_db  # teardown: patch context manager exits automatically
```

Use `autouse=True` sparingly — only for fixtures that must apply to every test in a scope (e.g., setting an environment variable):

```python
@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
```

## Time

Prefer `freezegun` for freezing wall-clock time. Fall back to `unittest.mock.patch` for targeted `datetime` mocking.

```python
from freezegun import freeze_time

@freeze_time("2024-01-15T12:00:00Z")
def test_expires_after_30_days():
    token = create_token()
    assert token.expires_at == "2024-02-14T12:00:00Z"

# Alternative: patch datetime directly
@patch("src.services.tokens.datetime")
def test_token_timestamp(mock_dt):
    mock_dt.utcnow.return_value = datetime(2024, 1, 15, 12, 0, 0)
    token = create_token()
    assert token.created_at == datetime(2024, 1, 15, 12, 0, 0)
```

## Setup Files

`tests/conftest.py` is the Python equivalent of a global setup file. Use the conftest hierarchy — place fixtures at the narrowest scope that covers all consumers:

- `tests/conftest.py` — project-wide (environment variables, logging configuration)
- `tests/unit/conftest.py` — all unit tests
- `tests/unit/api/conftest.py` — API layer only
- `tests/unit/services/conftest.py` — service layer only

The session-scoped `_test_environment` fixture ensures `ENVIRONMENT=test` is set before any test runs:

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session", autouse=True)
def _test_environment(monkeypatch_session):
    monkeypatch_session.setenv("ENVIRONMENT", "test")
```

## Reusable Test Utilities

### Factory functions — `tests/unit/factories.py`

Use `create_*` prefix. Always accept `**overrides` and apply them at the end so callers can override any field.

```python
# tests/unit/factories.py

def create_user(**overrides) -> dict:
    base = {
        "id": "u-1",
        "name": "Alice",
        "email": "alice@example.com",
        "active": True,
    }
    return {**base, **overrides}

def create_payment(**overrides) -> dict:
    base = {
        "id": "pay-1",
        "amount": 100,
        "currency": "EUR",
        "status": "pending",
    }
    return {**base, **overrides}
```

### Shared fixtures — `tests/conftest.py` and `tests/unit/conftest.py`

Extract any mock setup that is used in more than one test class into a `conftest.py` at the appropriate scope. See the **Setup Files** section for the conftest hierarchy and the `_test_environment` fixture.

Example of a reusable mock fixture at unit scope:

```python
# tests/unit/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture()
def mock_db_client():
    with patch("src.repositories.base.get_db_client") as mock_get:
        mock_db = MagicMock()
        mock_get.return_value = mock_db
        yield mock_db
```

### Shared data files — `tests/fixtures/`

Store static JSON or YAML payloads in `tests/fixtures/`. Import them in test files or conftest fixtures.

```python
# tests/fixtures/users.py
import json
from pathlib import Path

def load_user_fixture(name: str) -> dict:
    path = Path(__file__).parent / "data" / f"{name}.json"
    return json.loads(path.read_text())
```

## Assertions

```python
# Value equality
assert result == {"id": "u-1", "name": "Alice"}

# Mock call verification
mock_db.execute.assert_called_once_with(query="SELECT ...", params={"id": "u-1"})
mock_notify.assert_not_called()

# Exception assertions
import pytest
with pytest.raises(ValueError, match="not found"):
    users.get_user(user_id="missing")

# Partial matching via standard library
from unittest.mock import ANY
mock_client.send.assert_called_once_with(payload=ANY, timeout=30)
```

Prefer `assert_called_once_with()` over `assert_called_with()` — the latter does not verify call count.

## Coverage & Parameterized Tests

- Aim for 90%+ (branch coverage enabled in `pyproject.toml`: `branch = true`)
- Run unit tests: `uv run pytest tests/unit`
- Run with coverage: `uv run pytest --cov=src --cov-report=term-missing tests/unit`
- When 3 or more test cases differ only by input and expected output, use `@pytest.mark.parametrize` — never copy-paste `def test_*` blocks

```python
import pytest
from src.services.rails import get_rail

@pytest.mark.parametrize(
    "currency,expected_rail",
    [
        ("EUR", "sepa"),
        ("USD", "ach"),
        ("GBP", "fps"),
    ],
    ids=["EUR→sepa", "USD→ach", "GBP→fps"],
)
def test_get_rail_by_currency(currency: str, expected_rail: str) -> None:
    assert get_rail(currency) == expected_rail
```

Test every code path:

- Happy path
- Error / exception paths
- Edge cases: empty strings, zero, `None`, unicode, truncation boundaries
- Branches that should NOT be taken (use `assert_not_called()`)

## NO-NOs

### Python-adapted rules

1. **Never put test logic in `__init__.py`** — only `test_*.py` files. pytest discovers `test_*.py`; logic in `__init__.py` is invisible to the runner.
2. **No `# type: ignore` to silence mock type errors** — use `create_autospec()` or proper typing. Silencing type errors masks signature mismatches that would catch real bugs.
3. **No explicit `timeout` parameter on individual tests** — use `pytest-timeout` config globally if needed. Per-test timeouts are fragile and hide real performance problems.
4. **No `time.sleep()` or `asyncio.sleep()` in tests** — mock time-dependent code. Sleeps make tests slow and non-deterministic.
5. **No duplicate `patch()` for the same target in the same test** — patch once, configure the mock. Duplicate patches shadow each other and produce confusing behavior.
6. **No `print()` statements** — use the `caplog` fixture or a loguru sink for log assertions. Print output clutters test runs and is not validated.
7. **Never import and call private functions (`_helper`) directly** — test through the public API. Testing privates couples tests to implementation details.
8. **No snapshot/regression testing via serialized file comparisons** — use explicit assertions. Snapshot files go stale silently and obscure what is actually being verified.
9. **No committed `@pytest.mark.skip` without a reason string explaining why** — unexplained skips accumulate and rot the test suite.
10. **Do not mock pure utility functions** (string transforms, math, data reshaping) — only mock I/O (DB, HTTP, Redis, filesystem). Mocking pure functions hides real bugs and makes tests less trustworthy.

### DRY and trust rules

1. **Never duplicate factory/builder logic across test files** — extract to `tests/unit/factories.py` or `tests/fixtures/`. DRY principle: one source of truth for test data construction.
2. **Never copy-paste mock setup between test classes** — extract to `conftest.py` fixtures at the right scope (`tests/` → `tests/unit/` → `tests/unit/api/`). Repeated mock setup drifts and creates maintenance burden.
3. **Never skip `@pytest.mark.parametrize` when 3+ tests differ only by input/expected** — parametrize them. Avoids copy-paste test bloat and makes adding new cases trivial.
4. **Never write tests that pass even when the code under test is broken (vacuous tests)** — tests must build trust. A test that cannot fail is worse than no test.
5. **Never rewrite a failing test to make it pass** — if a test fails, the code is suspect first. Bending tests to match broken behavior masks real problems and erodes trust.
6. **Never mask a failing assertion behind a broad `except Exception`** — let it propagate. Masking failures defeats the purpose of testing.
7. **No `print()` in tests** — use the `caplog` fixture or a loguru sink if you need log assertions.

## Post-Generation Review

After writing tests, verify this checklist before finishing:

- [ ] Every `if/else` branch, `raise`, and early `return` has a dedicated test
- [ ] Optional fields and `None` inputs have both truthy and falsy tests
- [ ] String transforms have edge case tests (truncation boundary, special chars, empty string, unicode)
- [ ] Duplicated builders across test functions extracted to `tests/unit/factories.py`
- [ ] Repeated mock setup across test classes extracted to `conftest.py`
- [ ] 3+ similar `def test_*` blocks with different inputs converted to `@pytest.mark.parametrize`
- [ ] Large inline dicts extracted to a named factory function or fixture
- [ ] No residual `assert True` or vacuous assertions that cannot fail
- [ ] `assert_called_once_with()` used (not `assert_called_with()`) where call count matters
- [ ] `@pytest.mark.skip` blocks have a reason string
