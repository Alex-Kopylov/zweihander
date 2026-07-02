# Integration Testing

## Scope

Write integration tests for real wiring: routes, dependency injection, services,
persistence/cache resources, and resource lifecycle behavior.

Place endpoint integration tests under mirrored `tests/integration/api/...`
paths. Add small integration coverage for one happy path per endpoint or major
flow, plus failures that depend on route, dependency, or resource wiring.
Cover route -> dependencies -> service -> persistence/cache wiring through the
real route stack.

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
