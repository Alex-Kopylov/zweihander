# Test Data Factories

Source: adapted from `aishajv/claude-everything` FastAPI test conventions.

## Rule

Use `factory_boy` factories for persisted test entities. Do not use pytest
fixtures as entity builders unless the project already has a stronger local
convention.

## Placement

- Put factories in `tests/factories/`.
- Use one factory file per domain/module.
- Export one factory class per entity, such as `UserFactory` or
  `TenantFactory`.
- Keep relationship creation inside factories when a valid entity requires it.

## Defaults

Factories should create valid, boring entities by default. Override only fields
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

Avoid random defaults. Do not use `factory.Faker` unless the test is explicitly
about varied generated data; randomness makes failures harder to read and
reproduce.

## Inline Values

Inline values inside a test should be visually distinct from factory defaults.
For UUIDs in test bodies, use realistic-looking values instead of the zeroed
factory-default pattern.

Good:

```python
user_id = UUID("a1b2c3d4-5678-9abc-def0-1234567890ab")
```

Factory defaults can use zeroed IDs because each test should run with isolated
state, such as transaction rollback or a fresh test container.
