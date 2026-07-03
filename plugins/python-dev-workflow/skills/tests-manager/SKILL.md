---
name: tests-manager
description: Use when writing, editing, adding, reviewing, or planning Python unit and/or integration tests, mocks, fixtures, pytest structure, or test coverage.
metadata:
  "references/unit-testing.md": "Load when writing, reviewing, or planning unit-test behavior, mocks, or branch coverage."
  "references/integration-testing.md": "Load when writing, reviewing, or planning integration-test behavior, real wiring, or resource isolation."
  "references/test-structure.md": "Load when choosing pytest directories, file names, or source-to-test mirroring."
  "references/factory-conventions.md": "Load when tests need reusable deterministic entity builders or persisted domain objects."
  "references/redis-testing.md": "Load only when tests involve Redis, cache services, queues, pub/sub, Lua, locks, or TTLs."
  "../../agents/unit-test-writer.md": "Use for substantial Python pytest unit-test generation."
  "../../agents/integration-test-writer.md": "Use for substantial Python pytest integration-test generation."
  "../../agents/test-unit-reviewer.md": "Use for read-only review of existing unit tests."
  "../../agents/test-runner.md": "Use for focused pytest execution and failure reporting."
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
| Service or repository behavior behind an interface | Required | Add when real dependency or query wiring matters |
| New or changed endpoint or feature | Required for local branches and edge cases | Required for real route, dependency, or resource wiring |
| Bug fix | Required reproduction test | Add only if the bug was caused by integration wiring |

For a new endpoint or feature in general, normally write both unit and
integration coverage.

## Reference Loading

Use the frontmatter metadata as the routing table. Load only the reference or
agent whose metadata value matches the current task, and skip the rest.

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
- Use deterministic helpers for reusable test entities.

## Delegation

Use metadata-listed agents when the caller needs substantial test generation,
read-only review, or focused pytest execution.

When both unit and integration tests are needed, use the same source change as
input for both writer agents and keep their scopes separate.

## Pre-Finish Checklist

- Every changed behavior has at least one focused test.
- Bug fixes include a regression test that would fail on the old behavior.
- Unit tests cover branches, guard clauses, exceptions, and edge values.
- Integration tests cover wiring-sensitive paths without repeating every unit
  case.
- Fixtures and reusable builders are reused instead of duplicated inline data.
- Task-specific references were loaded only when metadata matched the task.
- Focused pytest command has been run, or the reason it could not run is
  reported.
