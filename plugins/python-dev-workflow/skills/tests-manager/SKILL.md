---
name: tests-manager
description: Use when writing, adding, reviewing, or planning Python pytest tests, including unit tests, integration tests, FastAPI endpoint tests, factory_boy test data, Redis-backed code, conftest hierarchy, mocks, and deciding when a change needs both unit and integration coverage.
---

# Tests Manager

## Overview

Use this skill as the entry point for Python pytest work. It defines the shared
testing rules, then routes to focused references or agents only when the project
needs them.

## Coverage Routing

For a behavior change, decide the minimum useful coverage before writing tests:

| Change | Unit tests | Integration tests |
|---|---|---|
| Pure function, schema, validation, branch, or error handling | Required | Usually not needed |
| Service or repository behavior behind an interface | Required | Add when real DB/cache/query wiring matters |
| New or changed API endpoint | Required for handler/service branches | Required for route -> dependency -> persistence wiring |
| Redis cache, queue, lock, pub/sub, Lua, or TTL behavior | Required with `fakeredis` or injected fake | Required with real Redis/testcontainers when parity matters |
| Bug fix | Required reproduction test | Add only if the bug was caused by integration wiring |

For a new endpoint, normally write both:

1. Unit tests for validation, auth/permission branches, service calls, error
   mapping, and edge cases.
2. Integration tests for one happy path through the real route stack and any
   wiring-sensitive failure path.

## Reference Loading

Load only the references needed for the current task:

- `references/test-structure.md` - test directory layout, file placement, and
  how unit and integration trees mirror `src/`.
- `references/factory-conventions.md` - `factory_boy` conventions, deterministic
  defaults, and when to use factories instead of pytest fixtures.
- `references/redis-testing.md` - Redis fixtures, fakeredis, testcontainers,
  isolation, CI services, pub/sub, TTL, and Lua tests.
- `references/redis/*.md` - detailed Redis CI and isolation patterns when
  `redis-testing.md` points there.
- `examples/redis/` - working Redis pytest examples when implementing similar
  tests.

## Shared Pytest Rules

- Use `test_*.py`; do not use `.spec.*` or `*_test.py`.
- Mirror source paths under `tests/unit/` and `tests/integration/`; create
  directories only when adding tests in that area.
- Group tests with `class TestThing:` or `class TestMethodName:` when it helps
  scan related behavior.
- Name functions `test_condition_expected_result`; use descriptive snake_case
  and avoid vague names like `test_works`.
- Keep each test focused on one behavior. Split tests whose name needs "and".
- Use `@pytest.mark.parametrize` when three or more cases differ only by input
  and expected output.
- Put shared fixtures in the narrowest useful `conftest.py`.
- Put static payloads under `tests/fixtures/`.
- Use deterministic factories or builders for reusable test entities.

## Unit Test Rules

- Mock I/O boundaries, not pure functions.
- Use `unittest.mock` or `pytest-mock`; prefer `create_autospec()` when
  signatures matter.
- Patch the name used by the module under test.
- Mock DB, cache, and external API clients at the client-factory or injected
  dependency level; do not mock individual SQL strings or Redis commands unless
  that command is the behavior under test.
- Assert behavior and output first. Verify mock calls only when the interaction
  is the behavior.
- Use `pytest.raises(ExpectedError, match="...")` for exceptions.
- Freeze wall-clock time with `freezegun` or a narrow datetime patch.
- Avoid `time.sleep()` and `asyncio.sleep()` in tests.

## Integration Test Rules

- Mark integration tests with `pytestmark = pytest.mark.integration` when the
  project uses markers.
- Prefer real app wiring, real dependency injection, and real persistence/cache
  test resources.
- Keep endpoint integration tests small: one happy path per endpoint or major
  flow, plus only the wiring-sensitive failures.
- Use transaction rollback, disposable containers, test DBs, or key prefixes for
  isolation.
- Do not duplicate unit branch matrices in integration tests.

## Delegation

Use focused agents when the caller needs substantial test generation:

- `unit-test-writer` for unit tests, branch coverage, mocks, fixtures, and
  factories.
- `integration-test-writer` for route-to-persistence flows, real services,
  Redis/testcontainers, and endpoint smoke coverage.
- `test-unit-reviewer` for read-only review of existing unit tests.
- `test-runner` for focused pytest execution and failure reporting.

When both unit and integration tests are needed, use the same source change as
input for both writer agents and keep their scopes separate.

## Pre-Finish Checklist

- Every changed behavior has at least one focused test.
- Bug fixes include a regression test that would fail on the old behavior.
- Unit tests cover branches, guard clauses, exceptions, and edge values.
- Integration tests cover wiring-sensitive paths without repeating every unit
  case.
- Factories and fixtures are reused instead of duplicated inline data.
- Redis tests load `references/redis-testing.md` and use isolation appropriate
  to unit or integration scope.
- Focused pytest command has been run, or the reason it could not run is
  reported.
