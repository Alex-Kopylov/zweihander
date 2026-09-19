# repository-test-layout

## Purpose

Decides where a test lives in this repository and what it is allowed to read, so that every test validates the artifact a user installs rather than the authored source it was rendered from, and so that no test ships to a user.

## ADDED Requirements

### Requirement: Tests validate artifacts, not sources
A test SHALL reach plugin content through a rendered harness tree and SHALL NOT read the authored `plugins/` tree or any `.j2` file. The single exception is a test of the build layer itself, which lives under `tests/unit/plugin_maintenance/`: the build layer's subject matter is the authored tree and the template rules, so those tests read both.

#### Scenario: Skill content is asserted against the rendered tree
- **WHEN** a test asserts that a skill's instructions contain a passage
- **THEN** it reads the skill file from a rendered harness tree, where the file carries no template suffix and no unresolved template syntax

#### Scenario: Build-layer test reads the authored tree
- **WHEN** a test under `tests/unit/plugin_maintenance/` checks a template-authoring rule
- **THEN** it may read `plugins/` and `.j2` sources, because the build layer is what it tests

#### Scenario: A skill other than the adaptation skill never learns about templates
- **WHEN** any test outside `tests/unit/plugin_maintenance/` is read
- **THEN** it names no `.j2` file and no path under `plugins/`

### Requirement: All tests live in the root test tree
Every test in the repository SHALL live under the root `tests/` directory. No directory named `tests/` SHALL exist anywhere under `plugins/**`.

#### Scenario: A skill-local test directory is rejected
- **WHEN** a `tests/` directory is added under a plugin or one of its skills
- **THEN** the repository policy check fails and names the directory

#### Scenario: Every test is reached by the standard run
- **WHEN** the repository's test command runs
- **THEN** it collects every test in the repository, with no second suite left outside it

### Requirement: The test tree mirrors the source tree
The root `tests/` tree SHALL follow the repository's own layout convention: unit tests under `tests/unit/` and integration tests under `tests/integration/`, mirroring the structure of what they test, with directories created only as they are needed. Build-layer tests SHALL sit under `tests/unit/plugin_maintenance/`. Tests of a skill's scripts SHALL sit under `tests/unit/plugins/<plugin>/skills/<skill>/`. Assertions on rendered content SHALL sit under `tests/integration/rendered/`, and checks of repository-wide conventions that read no plugin content SHALL sit under `tests/integration/repo/`.

#### Scenario: A skill script test mirrors its skill's path
- **WHEN** a test covers a script belonging to a named skill of a named plugin
- **THEN** its file sits at the mirrored path under `tests/unit/plugins/`, and no directory is created for a plugin or skill that has no test

#### Scenario: Repeated file names across the mirrored tree still collect
- **WHEN** two mirrored directories each hold a test file of the same name
- **THEN** both are collected and run, and neither shadows the other

### Requirement: One harness fixture parametrizes every harness-dependent test
The test suite SHALL expose a `harness` fixture parametrized over the supported harnesses. The list of supported harnesses SHALL be a single top-level constant exported by the build package and derived from the harness-to-manifest mapping the renderer already carries; the test suite SHALL NOT restate the harness names. A test that applies to one harness only SHALL narrow the fixture with a marker taking that harness's name. Running the same test once per harness is the intended single run; running a test against the authored source in addition to the rendered artifact is forbidden.

#### Scenario: An unmarked harness test runs for every harness
- **WHEN** a test requests the `harness` fixture and carries no narrowing marker
- **THEN** it runs once per supported harness

#### Scenario: A marked test runs for its harness only
- **WHEN** a test carries the harness marker naming one harness
- **THEN** it runs once, for that harness

#### Scenario: Adding a harness needs no test-suite edit
- **WHEN** a harness is added to the renderer's harness-to-manifest mapping
- **THEN** every harness-parametrized test picks it up with no change to the test suite

### Requirement: The rendered fixture is a fresh render of the current sources
The test suite SHALL expose a `rendered` fixture: for the harness under test, a fresh distribution-stage render of the current `plugins/` tree into a temporary directory, returning that tree's root. The fixture SHALL reuse the renderer the build already calls rather than re-implementing it, SHALL be built once per harness per session, and SHALL NOT run the generation stage — the CI gate runs the full build before the tests. Tests SHALL reach every plugin file through this fixture.

#### Scenario: Rendered content reflects an uncommitted source edit
- **WHEN** a template under `plugins/` is edited and the suite runs without rebuilding `dist/`
- **THEN** tests that read the `rendered` tree see the edit

#### Scenario: The render happens once per harness
- **WHEN** many tests in one session request the `rendered` fixture for the same harness
- **THEN** the tree is rendered once and shared

#### Scenario: Committed published trees are not the tests' subject
- **WHEN** a test outside the build layer asserts something about plugin content
- **THEN** the content comes from the `rendered` fixture and no file of a committed published tree is read; whether those trees are current is checked by the build layer alone

### Requirement: LLM-backed tests are marked and skipped by default
A test that calls an LLM SHALL carry an `llm` marker and SHALL be skipped unless the run explicitly opts in through the suite's LLM option. The `llm` marker and the harness marker are orthogonal: a test that is both LLM-backed and harness-specific carries both.

#### Scenario: Default run skips LLM tests
- **WHEN** the suite runs without the LLM option
- **THEN** every `llm`-marked test is reported skipped and no LLM is called

#### Scenario: Opt-in run includes LLM tests
- **WHEN** the suite runs with the LLM option
- **THEN** `llm`-marked tests execute

#### Scenario: Both markers apply together
- **WHEN** a test carries both the `llm` marker and a harness marker
- **THEN** the LLM option governs whether it runs and the harness marker governs which harness it runs for

### Requirement: Harness selection option narrows a run
The suite SHALL accept an option naming one harness. With it, the run SHALL execute every test that does not depend on the harness, plus the harness-dependent tests for the named harness, and SHALL exclude the harness-dependent tests of every other harness. Without it, every harness runs.

#### Scenario: Narrowed run excludes the other harness
- **WHEN** the suite runs with the harness option naming one harness
- **THEN** no test executes for any other harness, and harness-independent tests still execute

#### Scenario: Narrowed run and a conflicting marker
- **WHEN** the harness option names one harness and a test is marked for a different one
- **THEN** that test does not execute

### Requirement: Markers are registered
Every marker the suite defines SHALL be registered in the pytest configuration, so an unknown-marker warning identifies a typo rather than a convention.

#### Scenario: A typo in a marker name surfaces
- **WHEN** a test carries a marker name the configuration does not register
- **THEN** the run reports the unknown marker

### Requirement: Template syntax is never asserted outside the build layer
A test of rendered content SHALL NOT assert the presence of template syntax. The one exception is a test whose subject is the template-authoring skill itself, `adapt-skill-for-ai-harness`: templates are that skill's subject matter, so a passage about them is the skill's content rather than an assertion about how the skill file was produced. The harness-format guarantee is carried entirely by three build-layer checks. Two walk a fresh render and compare each rendered file against the template it came from: one fails on another harness's callable names, the other on leftover template markers outside raw blocks. The third compares consecutive builds byte for byte.

#### Scenario: A rendered-content assertion names no template syntax
- **WHEN** a test asserts that a rendered skill instructs the reader to ask the user
- **THEN** it asserts the rendered wording, not the template expression that produced it

#### Scenario: Foreign vocabulary is still caught
- **WHEN** a template renders another harness's callable name into a tree
- **THEN** the build-layer foreign-name scan fails and names the file and the name

### Requirement: Policy checks guard the boundary
Build-layer policy checks SHALL enforce the boundary so that it cannot erode by an ordinary edit. No file under `tests/` outside `tests/unit/plugin_maintenance/` SHALL name a template suffix, or a path into the authored plugin tree in any of its spellings: the slash-bearing literal at a path root, or the quoted directory name joined onto the repository root, passed to `Path(...)`, or passed to `.joinpath(...)`. The two names that merely share the word stay legal — the Codex marketplace manifest under `.agents/plugins/`, and the `plugins` key every marketplace manifest stores its own plugin list under — as does the bare unquoted word, which prose and identifiers use constantly. No `tests/` directory SHALL exist under `plugins/**`. Both checks SHALL name the offending file.

#### Scenario: A test pointed back at a template fails the check
- **WHEN** a test outside the build layer is edited to read a `.j2` file
- **THEN** the policy check fails and names that file

#### Scenario: A test pointed back at the authored tree fails the check
- **WHEN** a test outside the build layer is edited to build a path under `plugins/`
- **THEN** the policy check fails and names that file
