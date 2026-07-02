# Test Structure

Source: adapted from `aishajv/claude-everything` FastAPI test conventions.

## Rule

Mirror the `src/` package structure under both `tests/unit/` and
`tests/integration/`.

Create folders only when adding tests for that area; do not pre-create empty
trees.

## Layout

```text
tests/
  conftest.py
  factories/
    __init__.py
    users.py
  fixtures/
  unit/
    api/
      routes/
        users/
          test_user.py
      schemas/
        users/
          test_user.py
      middleware/
        test_auth.py
    services/
      users/
        test_user.py
    domain/
      entities/
      exceptions/
      types/
    persistence/
      models/
      repositories/
    core/
      test_config.py
  integration/
    api/
      users/
        test_user.py
```

## Unit Tests

- Place `src/services/users/user.py` tests in
  `tests/unit/services/users/test_user.py`.
- Place `src/api/routes/users/user.py` handler tests in
  `tests/unit/api/routes/users/test_user.py`.
- Place Pydantic schema tests under the mirrored `tests/unit/api/schemas/...`
  path.
- Place repository and model tests under the mirrored `tests/unit/persistence/`
  path. These can use a real DB if that is the local convention for persistence
  unit tests.

## Integration Tests

- Place endpoint integration tests under `tests/integration/api/...`.
- Cover route -> dependencies -> service -> persistence/cache wiring.
- Keep integration coverage intentionally small: one happy path per endpoint or
  major flow, plus failures that depend on real wiring.

## Naming

- Files: `test_{module}.py`.
- Classes: `TestThing` or `TestMethodName`.
- Functions: `test_condition_expected_result`.

If the first test for a module requires a missing mirror directory, create that
directory as part of the test change.
