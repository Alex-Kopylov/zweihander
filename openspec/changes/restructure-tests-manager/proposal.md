# Proposal: restructure-tests-manager

## Why

`python-dev-workflow:tests-manager` mixes rules, routing, and orchestration in
one 229-line `SKILL.md`, and every one of its five agents preloads that whole
file through `skills: [tests-manager]`. Cross-cutting rules have no single
owner:

- mocking guidance lives in 8 places;
- isolation guidance lives in 8 places;
- naming and placement live in 7 places;
- fixtures and test data live in 7 places;
- level selection lives in 7 places.

Two contradictions follow from this spread. There are two function-name
templates, and a "cover every branch in unit tests" rule fights the test
pyramid. There is also no way to judge or remove low-value tests, no
independent review of freshly written tests, and no structured agent output.
openclaw's `test-audit` skill (MIT, `openclaw/openclaw@bf636cc`) supplies the
missing value bar and audit method.

## What Changes

- **Lean skill, fat references.** `SKILL.md` becomes the orchestrator:
  - it recognises the intent (write or change, review, audit);
  - it runs that intent's pipeline;
  - it cuts lanes;
  - it holds no rule text.

  Everything else becomes a reference loaded only when its step or condition
  applies.
- **Workflows describe one step and call nothing.** They live in
  `references/workflows/`:
  - `write.md` covers TDD, the authoring gate, and level selection;
  - `review.md` covers a diff: conformance, gaps against requirements, and a
    low deletion bar;
  - `audit.md` covers an area: lanes, full evidence, a high deletion bar,
    mutation proof, and handoff.
- **Shared rules, stated once.** They live in `references/rules/`:
  - `test-value.md` holds the value bar, the junk patterns, and the retention
    bar, adapted from openclaw;
  - `mocking.md` holds the anti-patterns, ported from TypeScript to Python and
    merged with the mocking boundaries;
  - `conventions.md` holds naming, placement, fixtures, builders, and
    isolation;
  - `rationalizations.md` stays as it is.
- **Levels and domains.**
  - `references/levels/{unit,integration,e2e}.md` say what each level owns.
  - `references/domains/{celery,redis}.md` keep the existing Celery and Redis
    material, examples included.
- **Three agents, none preloading the skill.**
  - `test-scenario-planner` keeps its role.
  - `test-writer` is one writer for any level, and loads only that level's
    references.
  - `test-assessor` is a read-only judge of one lane in a fresh context. It
    serves review and audit, including the post-deletion recheck.
- **BREAKING (plugin consumers):** four agents are removed:
  - `test-runner`, because current models find and run tests unaided;
  - `unit-test-writer` and `integration-test-writer`, merged into
    `test-writer`;
  - `test-unit-reviewer`, replaced by `test-assessor` and `review.md`.
- **Isolation by construction.** Two rules are enforced by how agents are
  dispatched, not by prose:
  - a reviewer receives only the diff and the requirements, never the writer's
    reasoning;
  - audit edits have a single writer.
- **Three output contracts** live in `references/schemas/`:
  `scenarios.schema.json`, `ledger.schema.json`, and `handoff.schema.json`.
  Run results use pytest's built-in `--junitxml`.
- **Mutation proof by code.** It runs `mutmut` through `uv run --with mutmut`,
  targeted at owner functions. It is required whenever an audit deletes or
  merges tests.
- **Resolved contradictions.**
  - One naming template remains: `test_condition_expected_result`.
  - A branch needs unit coverage only when no test at any layer owns it.
- **Not carried over from openclaw:**
  - landing and PR flow;
  - Vitest, crabbox, and repository scripts;
  - Telegram and `extensions/` examples;
  - line-cap baselines;
  - merge-versus-rebase reconciliation;
  - a separate preservation-review format.

## Capabilities

### New Capabilities

- `tests-manager-orchestration`: the capability covers:
  - intent routing and the per-intent pipelines;
  - lane cutting;
  - the agent roles and their isolation;
  - progressive loading;
  - the single-owner rule references;
  - the review and audit semantics;
  - the output contracts and the mutation proof.

### Modified Capabilities

None. No existing spec covers plugin skill content.

## Impact

- `plugins/python-dev-workflow/skills/tests-manager/`:
  - `SKILL.md.j2` is rewritten;
  - `references/` is reorganised into `workflows/`, `rules/`, `levels/`,
    `domains/`, and `schemas/`;
  - `evals/evals.json` is updated;
  - `examples/` moves under the domain it serves.
- `plugins/python-dev-workflow/agents/`:
  - two agents are added: `test-writer.md` and `test-assessor.md`;
  - `test-scenario-planner.md` is kept;
  - four agents are deleted.
- `plugins/python-dev-workflow/skills/celery-expert/SKILL.md`: the link path
  to Celery testing is updated.
- `tests/integration/rendered/python_dev_workflow/test_plugin.py` is rewritten
  for the new layout. New tests are added for:
  - link and anchor resolution;
  - schema validity;
  - agreement between the junk-pattern ids and their headings.
- Example references to the removed `test-runner` are updated in
  `ai-assistant-ops:adapt-skill-for-ai-harness` and
  `work-session-tools:task-management`.
- `third_party/` gets an openclaw MIT notice and a license copy, and the
  Superpowers row for tests-manager is updated.
- Versioning: `python-dev-workflow` is bumped in both runtime manifests and
  both marketplace files, `README.md` agent table is updated, and `dist/` is
  rebuilt.
