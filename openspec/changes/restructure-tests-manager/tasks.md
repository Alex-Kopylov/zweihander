# Tasks: restructure-tests-manager

The order is guard-first: the repository tests that pin the new layout come
first and fail, then the content moves and turns them green. Author only under
`plugins/`, and rebuild `dist/` at the end.

## 1. Guards (fail first)

- [x] 1.1 Rewrite `tests/integration/rendered/python_dev_workflow/test_plugin.py` for the D1 layout:
  - metadata paths resolve for `SKILL.md`, `test-writer.md`, and `test-assessor.md`;
  - the contract checks are kept: E2E safety, level order, and planner scope;
  - phrase greps that only pinned old wording are dropped.
- [x] 1.2 Add a rendered test: every relative Markdown link in python-dev-workflow resolves, and every `#anchor` matches a heading slug.
- [x] 1.3 Add a rendered test: the ledger `junk_patterns` enum equals the `###` anchors under `rules/test-value.md#junk-patterns`.
- [x] 1.4 Add a rendered test covering three things:
  - no python-dev-workflow agent declares a `skills` preload of `tests-manager`;
  - neither harness tree contains `test-runner`, `unit-test-writer`, `integration-test-writer`, or `test-unit-reviewer`;
  - neither tree contains `vitest`, `crabbox`, `check-changed`, `autoreview`, `telegram`, or `extensions/`.
- [x] 1.5 Add `tests/unit/plugins/python-dev-workflow/skills/tests-manager/test_schemas.py`, mirroring md-bloat-hunter. Every schema must pass its metaschema and accept a minimal valid instance. The test must also check that an audit `D` entry without evidence fails, a `C` entry without `absorbed_by` fails, and an `F` entry without `repair` fails.
- [x] 1.6 Confirm that 1.1–1.5 fail for the expected reasons, not with errors.

## 2. Shared rules

- [x] 2.1 Write `references/rules/test-value.md`: the value bar, the 16 D6 junk patterns (one `###` per id, each with a pytest example), and the retention bar, adapted from openclaw.
- [x] 2.2 Write `references/rules/mocking.md`. Port AP1–AP4 and "When Mocks Become Too Complex" to Python and pytest, then merge in the mocking boundaries from `unit-testing.md`.
- [x] 2.3 Write `references/rules/conventions.md`. Merge Shared Pytest Rules, `test-structure.md`, `factory-conventions.md`, and the isolation and determinism rules. Keep the single naming template `test_condition_expected_result`.
- [x] 2.4 Move `rationalizations.md` to `references/rules/`, dropping any content now owned elsewhere.

## 3. Levels and domains

- [x] 3.1 Write `references/levels/unit.md`, `integration.md`, and `e2e.md.j2` from the current level references. Keep only what each level owns; link to `rules/` for shared content. The branch rule becomes "only branches no layer owns".
- [x] 3.2 Move the Celery material into `references/domains/`: `celery-testing.md` becomes `celery.md`, and its examples move under `domains/examples/celery/`.
- [x] 3.3 Move the Redis material into `references/domains/`: `redis-testing.md` becomes `redis.md`, `redis/*` moves to `domains/redis/`, and the examples move under `domains/examples/redis/`. Remove the duplicated Test Structure and marker sections from `redis.md` in favour of links.
- [x] 3.4 Update the Celery testing link in `skills/celery-expert/SKILL.md`.

## 4. Workflows, schemas, orchestrator

- [x] 4.1 Write `references/workflows/write.md`. It holds the TDD cycle (Verify RED and GREEN on the focused test), the authoring gate from the spec, level selection, and the checklist. It dispatches nothing.
- [x] 4.2 Write `references/workflows/review.md`. It covers conformance, gaps against requirements, the low deletion bar, and a ledger in `review` mode. It dispatches nothing.
- [x] 4.3 Write `references/workflows/audit.md`. It holds:
  - baseline via `pytest --junitxml`;
  - the evidence-first ledger with the high bar;
  - keepers and single-writer edits that delete unlocked seams;
  - the D8 mutmut procedure and a `recheck`-mode assessor;
  - handoff and validation (`git diff --check`, and `git diff --numstat` split into production and tests).
- [x] 4.4 Write the three `references/schemas/*.schema.json` files per D7.
- [x] 4.5 Rewrite `SKILL.md.j2` as the orchestrator. It holds:
  - the intent triggers in the description;
  - the intent table and the three pipelines, with the review loop and its iteration limit;
  - the D4 lane rule and the audit lane-plan confirmation;
  - the dispatch contract per agent, which gives the reviewer only the diff and requirements;
  - the run directory and schema validation;
  - the one-sentence Iron Law;
  - the metadata for workflows, rules, levels, domains, and agents.

  Do not prescribe who writes.

## 5. Agents

- [x] 5.1 Write `agents/test-writer.md`. It takes a level parameter, declares references per D3, has no skill preload, and returns changed files and the command it ran.
- [x] 5.2 Write `agents/test-assessor.md`. It is read-only, takes a `review`, `audit`, or `recheck` mode, and receives one lane. It declares references per D3, has no skill preload, and returns a ledger.
- [x] 5.3 Update `agents/test-scenario-planner.md`: remove the skill preload and return output per `scenarios.schema.json`.
- [x] 5.4 Delete `agents/test-runner.md`, `unit-test-writer.md`, `integration-test-writer.md`, and `test-unit-reviewer.md`, and the old flat reference files.
- [x] 5.5 Replace the `test-runner` example references in `ai-assistant-ops/skills/adapt-skill-for-ai-harness/SKILL.md` and `work-session-tools/skills/task-management/SKILL.md.j2` with an agent that exists.

## 6. Evals

- [x] 6.1 Retarget the existing cases in `skills/tests-manager/evals/evals.json` to the new layout, and add the four D10 cases.

## 7. Provenance, versions, docs, build

- [x] 7.1 Add `third_party/openclaw-LICENSE.txt` and a `THIRD_PARTY_NOTICES.md` section pinned to `bf636cc1bcdd59e65d5074a1bc309d903bf18e65`, covering `rules/test-value.md` and `workflows/audit.md`. Update the Superpowers tests-manager row (mocking ported to Python) and the `third_party/README.md` inventory.
- [x] 7.2 Bump the `python-dev-workflow` version with the version-bumper skill: both plugin manifests and both marketplace files. The change is breaking because agents are removed.
- [x] 7.3 Update `README.md`: the python-dev-workflow description and the agent table (three agents).
- [x] 7.4 Run `uv run python -m plugin_maintenance.build` and commit `dist/` with the sources.

## 8. Verification

- [x] 8.1 Run `uv run pytest tests`; everything passes, including the group 1 guards.
- [x] 8.2 Run `jq empty` on the marketplace files, every `plugin.json`, and the new schemas; then run `git diff --check`.
- [x] 8.3 Run `uv run python -m plugin_maintenance.build --check` and confirm there is no drift.
