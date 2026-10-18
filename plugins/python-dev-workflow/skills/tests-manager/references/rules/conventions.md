# Conventions

Follow the project's existing conventions first. These rules apply where the
project has none.

## Placement

- Put unit and integration tests under `tests/unit/` and `tests/integration/`,
  mirroring the `src/` package path:
  `src/services/users/user.py` → `tests/unit/services/users/test_user.py`.
- Organize `tests/e2e/` by externally observable journey, not by source module:
  `tests/e2e/<journey>/test_<flow>.py`.
- Create a directory only when adding its first test; do not pre-create empty
  trees.

```text
tests/
  conftest.py
  factories/
    users.py
  fixtures/
  e2e/
    checkout/
      test_checkout.py
  integration/
    api/
      users/
        test_user.py
  unit/
    api/
      routes/
        users/
          test_user.py
    services/
      users/
        test_user.py
```

## Naming

- Files: `test_<module>.py`. Do not use `*_test.py` or `.spec.*`.
- Classes: `class TestThing:` or `class TestMethodName:` when grouping helps
  scan related behavior.
- Functions: `test_condition_expected_result`, in descriptive snake_case, such
  as `test_expired_link_is_rejected`. Avoid vague names like `test_works`.

## Shape

- One coherent behavior per test. Split a test whose name needs "and".
- Use `@pytest.mark.parametrize` when cases differ only by input and expected
  output, and give each row a distinct reason to exist.
- Assert explicit expected values. `assert result` or `assert result is not
  None` is too weak when the value is known.
- Use `pytest.raises(ExpectedError, match="...")` for exceptions, checking both
  type and message where the message is part of the contract.
- Use `caplog` for log assertions, not `print`.
- A committed `@pytest.mark.skip` or `xfail` carries a `reason=`.

## Fixtures and test data

- Put shared fixtures in the narrowest `conftest.py` that covers their users,
  and reuse an existing fixture or helper before writing a new one.
- Put static payloads under `tests/fixtures/`.
- Use small deterministic builders for reusable entities, in `tests/factories/`,
  `tests/builders/`, or the project's existing helper location, such as
  `build_user()` or `UserBuilder`. A builder creates a valid, boring entity by
  default, including any relationship that validity requires; a test overrides
  only the fields that matter to its behavior.

Builder defaults are fixed and obviously fake:

| Field type | Default |
|---|---|
| UUID | `UUID("00000000-0000-0000-0000-000000000001")` |
| Email | `"test@test.com"` |
| Name | `"Test User"`, `"Test Tenant"` |
| Decimal or number | `Decimal("0")`, `0` |
| Identifier string | `"test_value"` |
| Hash | `"0" * 64` |
| Boolean | the neutral valid value, usually `True` for `is_active` |
| Enum | the first or most common valid variant |

Do not use random or faker-generated defaults unless varied data is the subject
of the test. Inline values in a test body look visibly different from builder
defaults, for example `UUID("a1b2c3d4-5678-9abc-def0-1234567890ab")`.

## Isolation and determinism

- Tests do not depend on execution order or share mutable state. Fixtures are
  function-scoped unless a wider scope is safe and needed, and every fixture
  that acquires a resource releases it after `yield`.
- Each test gets isolated state: transaction rollback, a fresh container or
  database, a dedicated key prefix, or `tmp_path`.
- No real wall-clock time, randomness, or external services. Freeze time with
  `freezegun` or a narrow patch of the name the module uses, and seed or inject
  randomness.
- Do not sleep. Wait for an observable condition with a timeout.
