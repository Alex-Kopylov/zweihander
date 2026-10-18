# Design: restructure-tests-manager

## Context

See `proposal.md` for motivation and `specs/tests-manager-orchestration/spec.md`
for requirements. The measured current state was taken at `865bbcc` and
visualised during planning.

- `SKILL.md.j2` (229 lines) holds several things at once:
  - rules: the Iron Law, the gate, the pyramid, Shared Pytest Rules, and
    Mock-Only Pass;
  - routing: 9 `metadata.references` and 5 `metadata.agents`;
  - the checklist.
- All five agents declare `skills: [tests-manager]`. In Claude Code this
  injects the full skill content into each agent at startup, per the Claude
  Code sub-agents documentation. So `test-runner` starts with the TDD rules
  and the level table.
- Across 15 rule topics, 11 are spread over three or more files. Two topics
  have no owner at all: low-value tests and agent output format.
  `test-unit-reviewer` appears in 8 topics and owns none of them; in 4 it
  repeats a rule and in 2 it contradicts one. `SKILL.md` contradicts itself:
  its checklist says "unit tests cover branches" while its pyramid says to
  select only the levels that add distinct evidence.
- The level and domain references (`integration`, `e2e`, `celery`, `redis`)
  only refine the shared rules and never conflict with them. The split by
  level and by domain already works.
- Upstream: `openclaw/openclaw@bf636cc1bcdd59e65d5074a1bc309d903bf18e65`,
  `.agents/skills/test-audit/` (SKILL.md 169 lines, CAMPAIGN.md 116 lines,
  MIT).

## Goals / Non-Goals

**Goals:**

- Each model sees only its step's context.
- No step is done twice.
- Every rule has one owner file.
- One entry point that picks its own workflow.

**Non-Goals:**

- A mutation-testing dependency in project templates. That work happens
  separately in `modern-python-template`.
- Language-neutral packaging. The skill stays pytest-specific.
- Prescribing who writes, the main session or `test-writer`. The agent
  decides; only the reviewer's isolation is fixed.
- Prose for things current models do unaided: finding and running tests,
  command flags, and report formatting.

## Decisions

### D1. Target layout

```text
skills/tests-manager/
  SKILL.md.j2                  orchestrator: intents, pipelines, lanes, dispatch
  references/
    workflows/write.md         TDD cycle, authoring gate, level selection, checklist
    workflows/review.md        diff lane: conformance, gaps, low deletion bar
    workflows/audit.md         area lanes: evidence, keepers, edits, mutmut, handoff
    rules/test-value.md        value bar, junk patterns, retention bar
    rules/mocking.md           mocking anti-patterns and boundaries (Python)
    rules/conventions.md       naming, placement, fixtures, builders, isolation
    rules/rationalizations.md  counter-arguments to skipping RED
    levels/unit.md             what unit owns
    levels/integration.md      what integration owns, markers, resource isolation
    levels/e2e.md.j2           journeys, safe resources, ask-user gate
    domains/celery.md          + domains/examples/celery/
    domains/redis.md           + domains/redis/*, domains/examples/redis/
    schemas/scenarios.schema.json
    schemas/ledger.schema.json
    schemas/handoff.schema.json
  evals/evals.json
agents/
  test-scenario-planner.md     requirements -> scenarios (kept)
  test-writer.md               writes tests at a given level
  test-assessor.md             judges one lane, read-only, fresh context
```

Only `SKILL.md` and `levels/e2e.md` need templating: they name harness
callables for dispatch and for the ask-user step. Every other file is plain
Markdown or JSON.

**Alternative rejected:** keep the current files and add an audit reference.
That adds a capability but leaves the 7–8-way duplication and the full-skill
preloads in place.

### D2. The skill is the only orchestrator

`SKILL.md` holds only the following:

1. The intent table, with triggers for write or change, review, and audit.
2. The pipelines:
   - `write` runs write then review, looping back to write on findings, with an
     iteration limit after which the user decides;
   - `review` runs review alone;
   - `audit` runs audit alone.
3. The lane-cutting rule (D4) and the dispatch contract: what each agent
   receives and what it returns.
4. The Iron Law as one sentence, because it governs whether the write
   pipeline is entered at all. The full cycle lives in `write.md`.

Workflow files never dispatch. `write.md` does not mention review. This keeps
each workflow reusable and lets the skill change a pipeline without touching
the steps in it.

**Alternative rejected:** `write.md` calls review itself. That puts
orchestration inside a step, and the owner rejected it explicitly.

### D3. Agents: three, declared references, no skill preload

| Agent | Receives | Loads via `metadata.references` | Returns |
|---|---|---|---|
| `test-scenario-planner` | requirements | none | `scenarios.schema.json` |
| `test-writer` | assigned scenario IDs, level, target paths | `levels/<level>.md`, `rules/conventions.md`, `rules/test-value.md`; `rules/mocking.md` when doubles are needed; `domains/*` when Celery or Redis is in play | changed files and the pytest command it ran |
| `test-assessor` | a lane (review: diff and requirements; audit: test paths and owners) and a mode (`review`, `audit`, or `recheck`) | `rules/test-value.md`, `rules/conventions.md`; `workflows/review.md` or `workflows/audit.md` by mode; `rules/mocking.md`, `levels/*`, and `domains/*` by condition | `ledger.schema.json` |

The agents are removed or replaced as follows:

- **`test-runner`** is removed. Every nudge it carried either already lives in
  `write.md` ("run the focused test" in Verify RED and GREEN) or is something
  models do unaided.
- **`unit-test-writer` and `integration-test-writer`** are merged into
  `test-writer`. Their bodies were identical; only the references they loaded
  differed. As a side effect, the plugin gains an E2E writer.
- **`test-unit-reviewer`** is replaced by `test-assessor` in `review` mode.
  Review of new tests and audit of old ones apply the same judgment to each
  test.

### D4. Lanes are cut by the orchestrator

The rule lives in `SKILL.md` and applies to review diffs and audit areas alike:

1. A mirrored path (`tests/{unit,integration}/<pkg>/…`) maps to the owner
   `<pkg>`.
2. A non-mirrored test maps to the owner whose code it imports most.
3. E2E tests map to their journeys.
4. An oversized owner is split into sub-modules, and small neighbouring owners
   are merged. The size threshold is stated in `SKILL.md` and calibrated on the
   first real audit; no number is guessed here.
5. An optional junk-sweep lane runs cheap mechanical patterns across the whole
   area, such as assertion-free tests and source greps.

For audits, the lane plan is shown before dispatch. Every in-scope file
belongs to exactly one lane.

### D5. Review versus audit

The per-test judgment is identical in both: the junk patterns, the retention
bar, and the ledger marks. The steps differ as follows:

| | review | audit |
|---|---|---|
| Scope source | diff, plus neighbouring tests of the same owners | area |
| Gaps against requirements | checked | not checked |
| Deletion bar | low: the author is present and nothing is accepted yet | high: full evidence is required |
| Editor | the write step, fed findings as a task | the orchestrator, as the single writer |
| Mutation proof | not needed | required after any deletion or merge |

openclaw's "focused audit" and "campaign" collapse into a single audit that
always works in lanes. A small area has one lane; a subsystem has many,
assessed in parallel. The campaign-only steps are triggered by what happens,
not by a mode:

- a baseline through `pytest --junitxml` is always recorded, because it is
  cheap;
- mutation proof and a recheck are required whenever something is deleted or
  merged;
- product defects are fixed separately when baseline failures survive into a
  keeper.

### D6. Shared rules

`rules/test-value.md` adapts openclaw's value bar, junk patterns, and
retention bar. Each junk pattern is a `###` heading whose anchor is its stable
id. The same ids form the ledger schema enum.

| Id | pytest example |
|---|---|
| `assertion-free` | calls the function, no `assert` |
| `self-comparison` | `assert m.model_dump() == m.model_dump()` |
| `copied-inventory` | hard-codes `__all__`, routes, or a registry |
| `source-grep` | `"x" in inspect.getsource(fn)` |
| `private-duplicate` | tests `_is_valid()` already proven via the public API |
| `duplicate-contract` | two tests or parametrize rows proving one branch |
| `shared-helper-replay` | each adapter re-tests the shared helper |
| `test-only-seam` | exists to keep `reset_cache_for_tests()` alive |
| `test-only-production-code` | production code whose only callers are tests |
| `oracle-from-subject` | expected value built by the code under test |
| `mock-implements-behavior` | `side_effect` re-implements the logic |
| `mock-only-pass` | asserts only that a mock returned or was called |
| `fixture-supplies-outcome` | a fixture pre-inserts the row the code must write |
| `restated-flag` | `assert settings.feature_x is True` |
| `unrelated-negative-control` | `pytest.raises(ValueError)` caught from a different guard |
| `overpromising-name` | the name promises more than the asserts check |

`rules/mocking.md` ports the four Superpowers anti-patterns from TypeScript to
Python and absorbs the boundaries section from `unit-testing.md`. The
`mock-only-pass` and seam entries in `test-value.md` link to it instead of
repeating it.

`rules/conventions.md` merges three sources: Shared Pytest Rules,
`test-structure.md`, and `factory-conventions.md`, plus the isolation rules
spread across the unit reference and the reviewer. It keeps the single naming
template `test_condition_expected_result` and removes the Redis reference's
own copy.

### D7. Output contracts

The schemas are flat draft 2020-12 JSON Schemas in the `md-bloat-hunter`
style. `if/then` makes the evidence fields required by mark.

- **`scenarios.schema.json`** has one field, `scenarios[]`. Each scenario has
  `id`, `requirement`, `actor_preconditions`, `action`, `expected`, and
  `corner_cases[]`, and the file also carries `gaps[]`.
- **`ledger.schema.json`** has `lane`, `mode` (`review`, `audit`, or
  `recheck`), `entries[]`, and `gaps[]`. The `gaps[]` field is used in review
  mode. Each entry has these fields:
  - `test_id`, `mark` (`R`, `F`, `C`, or `D`), `contract`, and `detects`;
  - `junk_patterns[]`, an enum of the D6 ids;
  - `non_test_callers[]`, `remaining_proof`, `absorbed_by`, and `repair`;
  - `history`, `unlocks[]`, `risk`, and `validation_command`.

  In audit mode, `D` requires the full evidence set, `C` requires
  `absorbed_by`, and `F` requires `repair`.
- **`handoff.schema.json`** has these fields:
  - `scope`, `lanes[]`, `baseline`, and `removed_categories[]`;
  - `owner_simplifications[]` and `retained_false_positives[]`;
  - `mutation_results[]`, `proof_runs[]`, and `loc {production, tests}`;
  - `ledger_files[]`, `follow_ups[]`, and `proposed_ownership_rules[]`.

The orchestrator validates each file with
`uvx check-jsonschema --schemafile <schema> <file>` and does not act on
invalid output. Agent outputs go to
`${ZWEIHANDER_TMP_DIR:-./.tmp/zweihander}/runs/tests-manager/<run-id>/`; the
run directory is kept and reported.

The preservation-review format from the previous plan is dropped. A recheck is
simply an assessor in `recheck` mode writing a ledger.

### D8. Mutation proof

- Targeted runs use `uv run --with mutmut mutmut run "<dotted.function>*"`.
  mutmut 3 copies sources into `mutants/` and never edits the checkout.
- Survivors come from `mutmut results`, and `mutmut show` prints a survivor's
  diff. `mutmut run` does not exit non-zero on survivors (mutmut #442), so the
  workflow reads `mutmut results` rather than the exit code.
- One mutmut process runs per checkout at a time.
- `mutants/` is deleted afterwards unless the project already ignores it.
- mutmut applies operator, constant, argument, and keyword mutations only.
  It never deletes a block. When a moved contract is a whole block of
  behaviour, the recheck assessor confirms by reading the keeper that it
  asserts that behaviour, and records the check in the ledger. No
  hand-editing of source is involved.

### D9. What is dropped from upstream

The following are not carried into the shipped tree:

- Landing and continuation.
- Vitest, crabbox, `check-changed.mjs`, `$autoreview`, and `scripts/pr`.
- Discovery paths hard-coded to openclaw's repository.
- Telegram and `extensions/telegram` examples.
- Line-cap baselines.
- The merge-versus-rebase reconciliation step.
- The preservation-review format.

Three lessons are kept as rules: judge a test by its assertions, not its
name; a retained test that fails on baseline is a product-bug lead; "static or
slow" is not a reason to delete.

### D10. Verification

- `test_plugin.py` is rewritten for the new layout. Contract checks are kept:
  E2E safety, the level order, and the planner's scope. Phrase greps that only
  pin old wording are dropped.
- New rendered tests check four things:
  - every relative Markdown link and anchor resolves;
  - the ledger junk enum equals the `###` anchors under
    `rules/test-value.md#junk-patterns`;
  - no agent declares `skills: [tests-manager]`;
  - none of the four removed agent names appear.
- A schema test mirrors md-bloat-hunter's: each schema passes its metaschema,
  a minimal valid instance passes, and a `D` entry without evidence fails.
- The evals keep the existing cases, retargeted, and add these:
  - an audit request yields a lane plan and evidence before any deletion;
  - a review request yields fresh-context assessors whose input is the diff
    only;
  - the gate rejects a source-grep test;
  - "delete the slow tests" stops at the retention bar.

## Risks / Trade-offs

- **Removing four agents breaks users who invoke them by name.**
  → Accepted, as there is no backward-compatibility policy. The change is
  called out as BREAKING, and the README agent table is updated.
- **A review loop could ping-pong between writer and reviewer.**
  → An iteration limit in `SKILL.md` stops it, and after the limit the user
  decides.
- **Lane size has no calibrated threshold yet.**
  → The first audit calibrates it, and the value lives in one place.
- **Writers no longer preload the skill, so they could miss a global rule.**
  → Every global rule the writer needs is a declared reference. The link test
  and the evals catch an omission.
- **Harness differences for dispatch and ask-user wording.**
  → They are confined to the two `.j2` files and resolved from the action
  matrix.
