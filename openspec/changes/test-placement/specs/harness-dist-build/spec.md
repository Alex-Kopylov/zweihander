# harness-dist-build

## ADDED Requirements

### Requirement: Repository tests never ship
A published harness tree SHALL contain no repository test files. Tests are development artifacts of this repository, not plugin content: a user who installs a rendered plugin receives a plain skill with no template traces and no tests. The rule is upheld at the authoring side — no `tests/` directory exists under `plugins/**` for the renderer to copy — rather than by a renderer filter, so a re-added skill-local test fails a policy check instead of being silently dropped from the published tree.

#### Scenario: No test directory in either tree
- **WHEN** the full build completes
- **THEN** no directory named `tests/` exists anywhere under `dist/claude-code/**` or `dist/codex/**`

#### Scenario: A re-added skill-local test is refused, not dropped
- **WHEN** a `tests/` directory is added under a plugin or one of its skills
- **THEN** the repository policy check fails and names the directory, rather than the build quietly omitting it

#### Scenario: An installed plugin carries no test that could fail
- **WHEN** a user installs a plugin from a published tree and runs a test collector inside it
- **THEN** it collects nothing, because the tree carries no tests that depend on the repository's authored sources
