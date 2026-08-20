---
name: tests-manager
description: Use when applying TDD to Python work, deriving test scenarios from requirements, or planning, writing, editing, reviewing, or running Python E2E, integration, or unit tests, including Celery, Redis, mocks, fixtures, pytest structure, or test coverage.
metadata:
  "references/e2e-testing.md": "Load when writing, reviewing, or planning externally observable business flows across the real system boundary."
  "references/integration-testing.md": "Load when writing, reviewing, or planning integration-test behavior, real wiring, or resource isolation."
  "references/unit-testing.md": "Load when writing, reviewing, or planning unit-test behavior, mocks, or branch coverage."
  "references/test-structure.md": "Load when choosing pytest directories, file names, or source-to-test mirroring."
  "references/factory-conventions.md": "Load when tests need reusable deterministic entity builders or persisted domain objects."
  "references/celery-testing.md": "Load only when tests involve Celery tasks, retries, canvas workflows, workers, brokers, result backends, or Beat schedules."
  "references/redis-testing.md": "Load only when tests involve Redis, cache services, queues, pub/sub, Lua, locks, or TTLs."
  "../../agents/test-scenario-planner.md": "Use when a task description, specification, or business requirement must be converted into test scenarios and corner cases."
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

## Scenario Discovery

When requirements need interpretation, use `test-scenario-planner` before
coverage routing. It owns what must be proven: requirement-linked scenarios,
negative paths, corner cases, assumptions, and specification gaps.

Tests Manager owns where and how to prove those scenarios: test-level selection,
authoring order, references, and writer-agent delegation. The planner does not
choose levels or write test code.

## Test Pyramid

Plan and author selected coverage from the outside in:

```text
E2E → Integration → Unit
```

Select only layers that add distinct evidence. Judge completeness by proven
requirement-linked scenarios and corner cases, not by test count or code
coverage percentage.

| Level | Owns | Select when |
|---|---|---|
| E2E | Externally observable business behavior across the complete system boundary | A user or external consumer must complete a real journey |
| Integration | Routes, dependency injection, services, queries, resources, and lifecycle wiring | Correctness depends on components working together |
| Unit | Local branches, validation, guards, exceptions, edge values, and decisions | Correctness can be isolated from system wiring |

For each scenario, first write or adapt E2E coverage, then integration coverage,
then unit coverage. Keep the RED-GREEN-REFACTOR loop for each selected layer;
do not implement lower-layer behavior before its higher-layer test is written.

## Reference Loading

Use the frontmatter metadata as the routing table. Load only the reference or
agent whose metadata value matches the current task, and skip the rest.

## Shared Pytest Rules

- Use `test_*.py`; do not use `.spec.*` or `*_test.py`.
- Follow existing project placement; otherwise use `tests/e2e/`,
  `tests/integration/`, and `tests/unit/` for their matching layers.
- Group tests with `class TestThing:` or `class TestMethodName:` when it helps
  scan related behavior.
- Name functions `test_condition_expected_result`; use descriptive snake_case
  and avoid vague names like `test_works`.
- Keep each test focused on one behavior. Split tests whose name needs "and".
- Use `@pytest.mark.parametrize` when cases differ only by input and expected
  output.
- Put shared fixtures in the narrowest useful `conftest.py`.
- Put static payloads under `tests/fixtures/`.
- Use deterministic helpers for reusable test entities.

## Common Mistake: Mock-Only Pass

Configuring a mock, asserting that it returned the configured value or received
a call, and claiming the test passed is cheating. It proves the mock
configuration, not the system behavior. Assert observable behavior from real
code; assert an interaction only when that interaction is the contract.

## Delegation

Use `test-scenario-planner` for scenario discovery only. Give its scenario
catalog to Tests Manager, which selects levels and passes the assigned scope to
writer agents.

Use the remaining metadata-listed agents for substantial layer-specific test
generation, read-only review, or focused pytest execution. Keep writer scopes
separate and do not let them expand the scenario catalog.

## Pre-Finish Checklist

- Every changed behavior has focused proof at the selected layer.
- Bug fixes have regression coverage that fails on the old behavior.
- Selected layers were authored E2E → Integration → Unit.
- E2E tests prove externally observable outcomes without duplicating lower
  layers.
- Integration tests prove wiring-sensitive paths without duplicating unit
  branches.
- Unit tests cover branches, guard clauses, exceptions, and edge values.
- Fixtures and reusable builders are reused instead of duplicated inline data.
- Task-specific references were loaded only when metadata matched the task.
- Focused pytest command has been run, or the reason it could not run is
  reported.
