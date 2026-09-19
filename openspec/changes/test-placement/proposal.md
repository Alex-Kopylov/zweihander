# Proposal: test-placement

Builds on `harness-dist-pipeline` (PR #68). Lands as a PR from `claude/test-placement` into `harness-dist-pipeline`.

## Why

`harness-dist-pipeline` made `plugins/` a source tree that nobody installs: users receive `dist/<harness>/`, rendered from `.j2` templates. The test suite did not follow. Seven files under `tests/` read `SKILL.md.j2` directly, some asserting Jinja syntax itself (`"{{ actions.AskUser | call }}" in skill`) — a claim about the template, not about anything a user ever runs. Commit `8c987e1` pointed `md-bloat-hunter`'s own tests at `SKILL.md.j2`, which is the same leak arriving from the other direction.

Meanwhile the skill-local tests under `plugins/*/skills/*/tests/` are in the worst possible place: CI never runs them (`pytest tests` only), the renderer copies them byte-for-byte into `dist/` and ships them to users, and two of them fail inside `dist/` because `SKILL.md.j2` does not exist there. A skill other than `adapt-skill-for-ai-harness` must not know `.j2` exists; that includes its tests.

## What Changes

- **Validate only artifacts.** Tests never read `plugins/` or any `.j2` file, with exactly one carve-out: tests of the build layer itself, which live in `tests/unit/plugin_maintenance/`.
- **BREAKING (for plugin consumers):** delete every `tests/` directory under `plugins/**` and move those tests into the root `tests/` tree. A rebuilt `dist/` no longer ships repository tests to users.
- Adopt the repo's own layout convention (`plugins/python-dev-workflow/skills/tests-manager/references/test-structure.md`): `tests/unit/` and `tests/integration/` mirroring the source tree, directories created only as needed.
  - `tests/unit/plugin_maintenance/` — build-layer tests (renderer, build `--check`, generators, action matrix, frontmatter matrix, source policy, CI gate). The only place allowed to read `plugins/` and `.j2`.
  - `tests/unit/plugins/<plugin>/skills/<skill>/` — tests of skill scripts, reaching the scripts through the `rendered` fixture.
  - `tests/integration/rendered/` — assertions on rendered content; `tests/integration/repo/` — repository conventions that touch no plugin content.
- **One mechanism, imported as a plain function.** Add `HARNESSES` to `plugin_maintenance/__init__.py`, derived from the existing `HARNESS_MANIFESTS` keys — never a fourth independent list of harness names. `tests/conftest.py` gains a parametrized session-scoped `harness` fixture, a session-scoped `rendered` fixture that calls the existing `render_tree()` into a temp dir, an `@pytest.mark.harness("<name>")` narrowing marker, an `@pytest.mark.llm` marker skipped by default, and `--harness` / `--llm` options. Both markers register in `pytest.ini`.
- **Delete Jinja-syntax assertions.** Every assertion checking template syntax in a rendered-content test is removed. Foreign-vocabulary coverage already lives in the dist invariant `test_rendered_files_carry_no_foreign_callable_names`; that, the leftover-marker scan, and byte-identical rebuilds are the whole harness-format check. The resume-tailoring "skill asks the user before proceeding" assertion is prompt behavior needing an LLM; it is deleted here.
- **Dist-invariant tests switch from reading committed `dist/` to reading `rendered`.** Committed `dist/` stays the CI gate's concern; the only tests that still answer for it are two build-layer ones, the freshness check (`stale_paths()`) and the byte-identical rebuild.
- **Two new source-policy tests** in `tests/unit/plugin_maintenance/`: no `tests/` directory under `plugins/**`, and no file under `tests/` outside `tests/unit/plugin_maintenance/` names a template suffix or a path into the authored tree in any of its spellings. Together they make a repeat of `8c987e1` a test failure.
- Consequences: rebuild and commit `dist/`; drop `tests/` from the md-bloat-hunter sentence "During normal invocation, `docs/` and `tests/` are skill-dev artifacts only."; bump `ai-assistant-ops` and `dev-workflow` (their shipped trees change); document the layout, fixtures, markers, options, and the boundary rule in `AGENTS.md`.

## Capabilities

### New Capabilities

- `repository-test-layout`: where a test lives, what it is allowed to read, the harness/rendered fixtures and the `harness`/`llm` markers and their options, and the policy checks that keep the boundary from eroding.

### Modified Capabilities

- `harness-dist-build`: a published plugin tree carries no repository tests. New requirement; the existing "Development files excluded" requirement is untouched, because this is an authoring rule enforced by a source-policy check, not a new renderer filter.

## Impact

- Tests: all 18 files under `tests/` move into the new layout; the 3 skill-local files under `plugins/**/tests/` move with them; `tests/conftest.py` gains the fixtures/markers/options and hands `fixture_repo`/`fixture_matrix` down to `tests/unit/plugin_maintenance/conftest.py`.
- Build tooling: `plugin_maintenance/__init__.py` gains `HARNESSES`. No renderer change.
- Config: `pytest.ini` registers both markers and sets `--import-mode=importlib` (the mirrored tree repeats file basenames).
- Shipped content: `dist/claude-code/**` and `dist/codex/**` lose four `tests/` directories; `ai-assistant-ops` and `dev-workflow` version bumps in both runtime manifests.
- Docs: `AGENTS.md` Development Workflow gains the test layout and the boundary rule.
- CI: `.github/workflows/ci.yml` unchanged — it already runs the full build, the diff check, and `pytest tests`, and `llm` tests skip by default. The job name `gate` is a required status check and must not change.

## Non-Goals

- Migrating `evals/` to pytest, or writing the `llm`-marked evaluation that replaces the deleted resume-tailoring prompt assertion. `evals/` directories stay where they are.
- Resolving PR #68's merge conflicts with `main`.
- Changing the renderer's template rules.
