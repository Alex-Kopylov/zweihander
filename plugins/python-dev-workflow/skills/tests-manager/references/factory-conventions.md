# Test Data Builders

## Rule

Use small deterministic builders for persisted test entities. Prefer the
project's existing helper style when one exists; otherwise use plain functions
or lightweight classes.

## Placement

- Put reusable builders in `tests/factories/`, `tests/builders/`, or the
  project's existing helper location.
- Use one helper file per domain/module.
- Export one builder per entity, such as `build_user()` or `UserBuilder`.
- Keep required relationship creation inside builders when a valid entity
  requires it.

## Defaults

Builders should create valid, boring entities by default. Override only fields
that matter to the behavior under test.

Use fixed, obviously fake defaults:

| Field type | Default pattern |
|---|---|
| UUID | `UUID("00000000-0000-0000-0000-000000000001")` style |
| Email | `"test@test.com"` |
| Names | `"Test User"`, `"Test Tenant"` |
| Decimal or number | `Decimal("0")`, `0` |
| Identifier string | `"test_value"` |
| Description string | `"Test Description"` |
| Hash | `"0" * 64` |
| Boolean | Neutral valid value, usually `True` for `is_active` |
| Enum | First or most common valid variant |

Avoid random defaults. Do not use faker-style generated data unless the test is
explicitly about varied generated data; randomness makes failures harder to read
and reproduce.

## Inline Values

Inline values inside a test should be visually distinct from builder defaults.
For UUIDs in test bodies, use realistic-looking values instead of the zeroed
builder-default pattern.

Good:

```python
user_id = UUID("a1b2c3d4-5678-9abc-def0-1234567890ab")
```

Builder defaults can use zeroed IDs because each test should run with isolated
state, such as transaction rollback or a fresh test container.
