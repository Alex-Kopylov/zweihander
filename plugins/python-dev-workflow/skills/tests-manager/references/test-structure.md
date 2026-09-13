# Test Structure

## Rule

Mirror the `src/` package structure under each applicable `tests/unit/` and
`tests/integration/` suite. Organize `tests/e2e/` by externally observable
journey instead of source module.

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
  e2e/
    checkout/
      test_checkout.py
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
