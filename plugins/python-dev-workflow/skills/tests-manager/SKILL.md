---
name: tests-manager
description: Use when doing TDD, test-first development, red-green-refactor, or deriving test scenarios from requirements for Python work, or planning, writing, editing, reviewing, or running Python E2E, integration, or unit tests, including Celery, Redis, mocks, fixtures, pytest structure, or test coverage.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
  "references/e2e-testing.md": "Load when writing, reviewing, or planning externally observable business flows across the real system boundary."
  "references/integration-testing.md": "Load when writing, reviewing, or planning integration-test behavior, real wiring, or resource isolation."
  "references/unit-testing.md": "Load when writing, reviewing, or planning unit-test behavior, mocks, or branch coverage."
  "references/test-structure.md": "Load when choosing pytest directories, file names, or source-to-test mirroring."
  "references/factory-conventions.md": "Load when tests need reusable deterministic entity builders or persisted domain objects."
  "references/celery-testing.md": "Load only when tests involve Celery tasks, retries, canvas workflows, workers, brokers, result backends, or Beat schedules."
  "references/redis-testing.md": "Load only when tests involve Redis, cache services, queues, pub/sub, Lua, locks, or TTLs."
  "references/testing-anti-patterns.md": "Load when the test needs mocks, test doubles, or test-only helpers."
  "references/rationalizations.md": "Load when anyone argues for skipping the failing test or writing tests after the code."
  "../../agents/test-scenario-planner.md": "Use when a task description, specification, or business requirement must be converted into test scenarios and corner cases."
  "../../agents/unit-test-writer.md": "Use for substantial Python pytest unit-test generation."
  "../../agents/integration-test-writer.md": "Use for substantial Python pytest integration-test generation."
  "../../agents/test-unit-reviewer.md": "Use for read-only review of existing unit tests."
  "../../agents/test-runner.md": "Use for focused pytest execution and failure reporting."
---

# Tests Manager

## Overview

Use this skill as the entry point for Python pytest work, including test-first
development. It defines the shared testing rules, then routes to focused
references or agents only when the project needs them.

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you did not watch the test fail, you do not know if it
tests the right thing.

Violating the letter of the rules is violating the spirit of the rules.

## When to Use

Use for new features, bug fixes, refactoring, and behavior changes.

Ask your human partner before skipping TDD for throwaway prototypes, generated
code, or configuration files.

Thinking "skip TDD just this once"? That is rationalization. Load
`references/rationalizations.md`.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Scenario Discovery

When requirements need interpretation, use `test-scenario-planner` before
coverage routing. It owns what must be proven: requirement-linked scenarios,
negative paths, corner cases, assumptions, and specification gaps.

Tests Manager owns where and how to prove those scenarios: test-level selection,
authoring order, references, and writer-agent delegation. The planner does not
choose levels or write test code.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it and implement fresh from the test. Do not
keep it as reference, do not adapt it while writing the test, and do not look at
it. Delete means delete.

## Existing Code Gate

Before choosing a test:

1. Inspect the callers and existing tests for the behavior being changed.
2. If an existing test owns that contract, update it for the intended behavior.
   Do not add a parallel ad hoc test just to create RED.
3. If coverage is missing, add the focused case to the nearest responsible test
   suite and follow its existing conventions.
4. For a behavior-preserving refactor with adequate coverage, use the existing
   tests unchanged: verify the focused suite is green, refactor, then keep it
   green. Do not invent a failing test for unchanged behavior.

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

For each scenario, work one scenario at a time: first write or adapt E2E
coverage, then integration coverage, then unit coverage. Keep the
RED-GREEN-REFACTOR loop for each selected layer; do not implement lower-layer
behavior before its higher-layer test is written.

## Red-Green-Refactor

The cycle applies to one scenario at one level.

### RED - Write A Failing Test

Cover one coherent behavior. Name the test after that behavior. Use real code;
mock only when unavoidable.

### Verify RED - Watch It Fail

Mandatory. Run the focused test and confirm three things:

- It fails rather than errors.
- The failure message is the one you expected.
- It fails because the behavior is missing, not because of a typo.

Test passed? You are testing existing behavior. Fix the test.

Test errored? Fix the error and re-run until it fails correctly.

### GREEN - Write Minimal Code

Write the simplest code that passes the test. Do not add options, features, or
improvements the test does not require.

### Verify GREEN - Watch It Pass

Mandatory. Run the focused test and confirm the test passes, the other tests
still pass, and the output is clean.

Test still fails? Fix the code, not the test.

### REFACTOR - Clean Up

Only after green. Remove duplication, improve names, extract helpers. Keep the
tests green and add no behavior.

## Good Tests

| Quality | Good | Bad |
|---|---|---|
| Minimal | One coherent behavior. Split independently meaningful failures. | `test('validates email and domain and whitespace')` |
| Clear | The name describes the behavior | `test('test1')` |
| Shows intent | Demonstrates the desired API | Hides what the code should do |

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

## Debugging Integration

Found a bug? Write the failing test that reproduces it, then run the cycle. The
test proves the fix and prevents the regression. Never fix a bug without a test.

## When Stuck

| Problem | Solution |
|---|---|
| Do not know how to test | Write the wished-for API, then the assertion. Ask your human partner. |
| Test too complicated | The design is too complicated. Simplify the interface. |
| Must mock everything | The code is too coupled. Use dependency injection. |
| Test setup is huge | Extract helpers. Still complex? Simplify the design. |

## Delegation

Use `test-scenario-planner` for scenario discovery only. Give its scenario
catalog to Tests Manager, which selects levels and passes the assigned scope to
writer agents.

Use the remaining metadata-listed agents for substantial layer-specific test
generation, read-only review, or focused pytest execution. Keep writer scopes
separate and do not let them expand the scenario catalog.

## Pre-Finish Checklist

- Watched each test fail before implementing, for the expected reason.
- Wrote minimal code to pass each test.
- Every changed behavior has focused proof at the selected layer.
- Bug fixes have regression coverage that fails on the old behavior.
- Selected layers were authored E2E → Integration → Unit.
- E2E tests prove externally observable outcomes without duplicating lower
  layers.
- Integration tests prove wiring-sensitive paths without duplicating unit
  branches.
- Unit tests cover branches, guard clauses, exceptions, and edge values.
- Tests use real code, with mocks only where unavoidable.
- Fixtures and reusable builders are reused instead of duplicated inline data.
- Task-specific references were loaded only when metadata matched the task.
- Focused pytest command has been run, or the reason it could not run is
  reported, and the output is clean.

Cannot check every box? You skipped TDD. Start over.

## Final Rule

```
Production code → a test exists and failed first
Otherwise → not TDD
```

No exceptions without your human partner's permission.
