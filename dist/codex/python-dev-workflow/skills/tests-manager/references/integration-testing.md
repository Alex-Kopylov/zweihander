# Integration Testing

## Scope

Write integration tests for real wiring: routes, dependency injection, services,
persistence/cache resources, and resource lifecycle behavior.

Place endpoint integration tests under mirrored `tests/integration/api/...`
paths. Cover the wiring-sensitive success and failure paths assigned by Tests
Manager through the real route -> dependencies -> service ->
persistence/cache stack.

Integration tests may enter through a route, but they prove component wiring
and resource semantics. A complete externally observable business journey
belongs to E2E coverage.

## Boundaries

- Mark integration tests with `pytestmark = pytest.mark.integration` when the
  project uses markers.
- Prefer real app setup, real dependency injection, and real persistence/cache
  test resources.
- Use transaction rollback, disposable containers, dedicated test databases, or
  key prefixes for isolation.
- Do not duplicate every unit-test branch matrix.
- Do not replace real wiring with broad mocks unless the project already does so
  for integration tests.
- If unit branch coverage is missing, report the gap and suggest
  `unit-test-writer` rather than expanding integration tests into unit coverage.
