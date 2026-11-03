# Integration Level

## Owns

Real wiring: routes, dependency injection, services, queries, persistence and
cache resources, and resource lifecycle. An integration test may enter through a
route, but it proves that components work together and that resources behave as
the code assumes. A complete externally observable business journey belongs to
the E2E level.

Cover the wiring-sensitive success and failure paths through the real route →
dependencies → service → persistence or cache stack. Do not repeat the unit
branch matrix.

## Markers

When the project uses markers, mark the module:

```python
pytestmark = pytest.mark.integration
```

Register the marker so `--strict-markers` accepts it:

```toml
[tool.pytest.ini_options]
markers = ["integration: tests that need real resources"]
```

## Resource isolation

- Prefer the real app setup, real dependency injection, and real persistence or
  cache test resources.
- Isolate with transaction rollback, disposable containers, a dedicated test
  database, or key prefixes; see
  [isolation and determinism](../rules/conventions.md#isolation-and-determinism).
- Do not replace real wiring with broad mocks unless the project already does so
  for integration tests.
- Report a missing unit-level proof as a gap instead of expanding an
  integration test into branch coverage.
