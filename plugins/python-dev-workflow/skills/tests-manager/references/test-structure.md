# Test Structure

## Rule

Mirror the `src/` package structure under both `tests/unit/` and
`tests/integration/`.

Create folders only when adding tests for that area; do not pre-create empty
trees.

## Example Layout

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

## Naming

- Files: `test_{module}.py`.
- Classes: `TestThing` or `TestMethodName`.
- Functions: `test_condition_expected_result`.

If the first test for a module requires a missing mirror directory, create that
directory as part of the test change.
