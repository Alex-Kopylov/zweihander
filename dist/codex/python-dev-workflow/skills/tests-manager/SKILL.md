---
name: tests-manager
description: Use when writing, changing, reviewing, or auditing Python pytest tests, including TDD or red-green-refactor, deriving test scenarios from requirements, choosing E2E, integration, or unit coverage, mocks, fixtures, Celery or Redis tests, or finding low-value, duplicate, or implementation-coupled tests to prune.
metadata:
  references:
    "references/workflows/write.md": "Load in the write pipeline before writing or changing tests."
    "references/workflows/review.md": "Load only when no agent can be dispatched and you must review in this session."
    "references/workflows/audit.md": "Load in the audit pipeline."
    "references/rules/test-value.md": "Load when judging whether a test is worth adding, keeping, or deleting."
    "references/rules/conventions.md": "Load before choosing test names, paths, fixtures, or builders."
    "references/rules/mocking.md": "Load when a test needs mocks, fakes, or other test doubles."
    "references/rules/rationalizations.md": "Load when anyone argues for skipping the failing test or writing tests after the code."
    "references/levels/unit.md": "Load when unit tests are selected."
    "references/levels/integration.md": "Load when integration tests are selected."
    "references/levels/e2e.md": "Load when E2E tests are selected or run."
    "references/domains/celery.md": "Load only when tests involve Celery tasks, retries, canvas workflows, workers, brokers, result backends, or Beat schedules."
    "references/domains/redis.md": "Load only when tests involve Redis, cache services, queues, pub/sub, Lua, locks, or TTLs."
  agents:
    "../../agents/test-scenario-planner.md": "Use when requirements need interpretation before tests are written."
    "../../agents/test-writer.md": "Use to write tests at one assigned level."
    "../../agents/test-assessor.md": "Use to judge one lane in review, audit, or recheck mode."
---

# Tests Manager

The entry point for pytest work. It recognises the intent, runs that intent's
pipeline, and cuts lanes. Every rule lives in a reference; load one only when
its condition in `metadata` applies.

**Iron Law:** no production code without a failing test first.

## Intents

| Intent | Recognise by | Pipeline |
|---|---|---|
| Write | a feature, bug fix, or behavior change; TDD; "add tests for" | [write](#write-pipeline) |
| Review | "review these tests"; a diff of tests awaiting acceptance | [review](#review-pipeline) |
| Audit | "audit", "prune", or "clean up" tests; low-value, duplicate, or slow tests | [audit](#audit-pipeline) |

## Run directory

Create a private run directory for agent outputs:

```bash
run_dir="${ZWEIHANDER_TMP_DIR:-./.tmp/zweihander}/runs/tests-manager/$(date +%Y%m%dT%H%M%S)-$$"
mkdir -p -m 700 "$run_dir"
```

Write each agent's JSON output there and validate it before acting on it:

```bash
uvx check-jsonschema --schemafile <skill-dir>/references/schemas/<name>.schema.json "$run_dir/<file>.json"
```

Do not act on output that fails validation; dispatch the agent again with the
error. Keep the run directory and report its path.

## Write pipeline

1. **Scenarios.** When the requirements need interpretation, dispatch
   `test-scenario-planner` with the requirements only. Its output follows
   [scenarios.schema.json](references/schemas/scenarios.schema.json).
2. **Write.** Follow [write](references/workflows/write.md). The tests are
   written either in this session or by `test-writer`, one level per dispatch.
3. **Review.** Cut the diff into [lanes](#lanes) and dispatch one
   `test-assessor` per lane in `review` mode, in parallel.
4. **Loop.** Findings — any entry not marked `R`, and any gap — go back to step
   2 as a task, followed by a fresh review. After three review rounds with
   findings left, show them and ask the user with $request_user_input
   how to proceed.

## Review pipeline

Cut the diff into [lanes](#lanes) and dispatch one `test-assessor` per lane in
`review` mode, in parallel. Report the validated ledgers. Edit nothing unless
the user asks.

## Audit pipeline

Follow [audit](references/workflows/audit.md). This session is the only writer.

1. Record the baseline.
2. Cut the area into [lanes](#lanes), show the lane plan, and confirm it with
   $request_user_input before dispatching.
3. Dispatch one `test-assessor` per lane in `audit` mode, in parallel.
4. Build the layer plan from the validated ledgers and apply the edits.
5. If a test was deleted or merged: run the mutation proof, then dispatch a
   fresh `test-assessor` per changed lane in `recheck` mode. Restore or reject
   every gap it reports, and recheck again.
6. Fix product defects, validate, and write the handoff, validated against
   [handoff.schema.json](references/schemas/handoff.schema.json).

## Lanes

Partition the review diff or audit area by production owner. Every in-scope
test file belongs to exactly one lane; an assessor never picks its own.

1. A mirrored path such as `tests/unit/<pkg>/…` or `tests/integration/<pkg>/…`
   belongs to the owner `<pkg>`, so both suites of one package share a lane.
2. A test outside a mirrored path belongs to the owner whose code it imports
   most.
3. E2E tests belong to their journey.
4. Split an owner with more than about 1,500 lines of tests into sub-module
   lanes; merge neighbouring owners with under about 300 lines between them.
   These thresholds are a first estimate: recalibrate them after the first
   real audit.
5. An audit may add one junk-sweep lane that scans the whole area for
   mechanical patterns only, such as assertion-free tests and source greps.

## Dispatch contract

Dispatch with $spawn_agent. Give each agent only its own
input, and the run directory path when it must know where its output goes.

| Role | Receives | Returns |
|---|---|---|
| `test-scenario-planner` | the requirements | [scenarios](references/schemas/scenarios.schema.json) |
| `test-writer` | scenario ids, one level, target paths | changed files and the pytest command it ran |
| `test-assessor`, `review` | the lane's diff and the requirements or scenario catalog | [ledger](references/schemas/ledger.schema.json) |
| `test-assessor`, `audit` | the lane's test paths and owners | [ledger](references/schemas/ledger.schema.json) |
| `test-assessor`, `recheck` | the lane's diff and the mutmut survivors | [ledger](references/schemas/ledger.schema.json) |

A reviewing or rechecking assessor never receives this session's plan,
reasoning, transcript, or earlier ledgers.
