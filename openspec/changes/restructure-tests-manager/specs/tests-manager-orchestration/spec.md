## Purpose

Lets `python-dev-workflow:tests-manager` handle every pytest testing request —
writing, changing, reviewing, and auditing tests. It chooses its own pipeline,
gives each model only the context its step needs, and states every shared rule
exactly once.

## ADDED Requirements

### Requirement: Intent routing from one entry point
The tests-manager skill SHALL recognise three intents from the request:

- write or change tests;
- review tests;
- audit tests.

For each intent it SHALL run that intent's pipeline. The skill file SHALL hold
routing and orchestration only. It SHALL NOT restate any rule that a reference
owns.

#### Scenario: Audit request
- **WHEN** a user asks to audit a package's tests
- **THEN** the skill loads the audit workflow and neither the write nor the review workflow

#### Scenario: Write request
- **WHEN** a user asks for tests for a new feature
- **THEN** the skill runs the write step followed by the review step

### Requirement: Workflows describe one step and call nothing
Each workflow reference SHALL describe exactly one step (write, review, or
audit). Workflow references SHALL NOT dispatch other workflows or agents.
Sequencing and dispatch SHALL live in the skill file.

#### Scenario: Write step ends
- **WHEN** the write workflow's step is complete
- **THEN** control returns to the skill, which starts the review step; the write workflow itself names no reviewer

### Requirement: Progressive loading
Each agent SHALL declare, in its own metadata, the specific references it
needs. Each declaration SHALL carry a load condition. No agent SHALL preload
the tests-manager skill. A reference SHALL be loaded only when its step or
condition applies.

#### Scenario: Unit test writing
- **WHEN** the writer agent writes unit tests for code with no Celery or Redis use
- **THEN** its context holds the unit level reference, the shared conventions, and the test-value rules, and none of the integration, E2E, Celery, Redis, or audit material

#### Scenario: No skill preload
- **WHEN** any tests-manager agent file is read
- **THEN** it declares no `skills` preload of tests-manager

### Requirement: One owner per shared rule
Every rule used by more than one step or agent SHALL be stated once, in a rule
reference. Every other file that applies the rule SHALL link to it by file and
anchor. Every such link SHALL resolve in the rendered tree.

#### Scenario: Mocking guidance
- **WHEN** the write workflow, the review workflow, and the assessor need mocking guidance
- **THEN** each links to the mocking reference and none restates its content

#### Scenario: Broken anchor
- **WHEN** a rule heading is renamed and a link still points to the old anchor
- **THEN** a repository test fails and names the link

### Requirement: Single naming template and owned-branch coverage
The shared conventions SHALL define exactly one test-function naming template.
Unit coverage of a branch, guard clause, exception path, or edge value SHALL be
required only when no test at any layer owns it.

#### Scenario: Integration test owns a branch
- **WHEN** an integration test already proves a validation branch
- **THEN** neither the review nor the write checklist demands a unit test for it

### Requirement: Authoring gate
Before a new or changed test is added, the write workflow SHALL require all of
the following. If any answer is missing, the test SHALL NOT be added.

- The contract the test protects, and a credible regression that would fail
  it.
- No production seam that only tests need.
- No junk-pattern match, unless the retention bar names the contract the test
  independently guards.
- Resilience to behavior-preserving refactoring.

A bug fix SHALL add one regression test at the owner boundary. That test SHALL
fail on the pre-fix code.

#### Scenario: Source grep
- **WHEN** a proposed test asserts that source text contains a string, and no user-facing key, byte, or path depends on it
- **THEN** the gate rejects the test

#### Scenario: Multi-layer bug
- **WHEN** a bug crosses a route, a service, and a repository, and its cause is in the service
- **THEN** exactly one failing-first regression test is added at the service boundary

### Requirement: Lanes cut by the orchestrator
The orchestrator SHALL partition a review diff or an audit area into lanes by
production owner. It SHALL follow these rules:

- a mirrored test path maps to the owner it mirrors;
- a non-mirrored test maps to the owner it imports most;
- E2E tests map to journeys;
- an oversized owner is split into sub-modules;
- small neighbouring owners are merged.

Every in-scope test file SHALL belong to exactly one lane. The assessor SHALL
NOT choose its own lane. The audit SHALL present the lane plan before it
dispatches assessors.

#### Scenario: Mirrored layout
- **WHEN** an audit covers `tests/unit/billing/` and `tests/integration/billing/`
- **THEN** both belong to the single lane `billing`

#### Scenario: Two owners in a diff
- **WHEN** a diff touches tests for `billing` and `auth`
- **THEN** two assessors review in parallel, one per lane

### Requirement: Independent review in a fresh context
A reviewing assessor SHALL receive only the diff of its lane and the
requirements or scenario catalog. It SHALL NOT receive the writer's
transcript, plan, or reasoning. Review SHALL check two things:

- conformance with the shared rules;
- gaps against the requirements.

Review SHALL apply a low deletion bar. Findings SHALL return to the write step
as a task. A repeated review SHALL run up to an iteration limit, and after that
limit the user decides. Who writes — the main session or the writer agent — is
left to the agent's judgment; no instruction prescribes it.

#### Scenario: Reviewer input
- **WHEN** the review step starts after the main session wrote tests itself
- **THEN** the assessor's input contains the diff and the requirements and nothing from the main session's reasoning

### Requirement: Evidence-first audit
An audit SHALL always work in lanes, whether the area has one lane or many. It
SHALL record a baseline with pytest's JUnit XML output. An existing test SHALL
NOT be deleted, merged, or repaired until its ledger entry records all of the
following:

- the failure the test detects;
- the non-test callers;
- the remaining stronger proof, or the reason no proof is needed;
- the history;
- the deletions the change unlocks;
- the risk;
- a validation command.

Audit edits SHALL have a single writer, the orchestrator. Those edits SHALL
delete the test-only seams they unlock.

#### Scenario: Missing evidence
- **WHEN** a ledger entry marked for deletion lacks the remaining-proof field
- **THEN** it fails schema validation and the test is kept

#### Scenario: Slow test
- **WHEN** the only argument for deletion is that a test is slow or static
- **THEN** the retention bar keeps it unless a junk pattern applies with full evidence

### Requirement: Mutation proof after deletions
Whenever an audit deletes or merges tests, it SHALL run `mutmut` against the
owner functions whose contracts moved. It SHALL then have a fresh-context
assessor, which never saw the deletion reasoning, confirm that every contract
kept a test. The recheck SHALL use the ledger format. A surviving mutant SHALL
count as a gap unless the assessor shows it is equivalent. Mutation runs SHALL
NOT modify the checkout's source files.

#### Scenario: Merged tests
- **WHEN** two tests are merged into a keeper
- **THEN** mutants of the owning function are run and none survives unexplained before the audit reports completion

### Requirement: Output contracts
The following outputs SHALL each validate against a JSON Schema shipped with
the skill:

- the scenario planner's output;
- the assessor's ledger;
- the audit handoff.

Output that fails validation SHALL NOT be acted on.

#### Scenario: Invalid ledger
- **WHEN** an assessor returns an entry marked `C` without the absorbing owner
- **THEN** validation fails and the entry is not applied

### Requirement: Removed agents
The plugin SHALL NOT ship the following agents:

- `test-runner`;
- `unit-test-writer`;
- `integration-test-writer`;
- `test-unit-reviewer`.

No shipped file SHALL refer to them.

#### Scenario: Rendered tree scan
- **WHEN** both rendered trees are searched for the four removed agent names
- **THEN** no match is found

### Requirement: No upstream repository specifics
The shipped tree SHALL NOT contain any of the following:

- openclaw landing or continuation guidance;
- openclaw tooling names;
- Telegram or `extensions/` examples;
- line-cap baselines;
- merge-versus-rebase guidance.

#### Scenario: Rendered tree scan
- **WHEN** the rendered python-dev-workflow tree is searched for `vitest`, `crabbox`, `check-changed`, `autoreview`, `telegram`, and `extensions/`
- **THEN** no match is found
