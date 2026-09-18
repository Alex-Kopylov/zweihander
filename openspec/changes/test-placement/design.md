# Design: test-placement

## Context

See `proposal.md` for motivation. This change builds on `harness-dist-pipeline` (PR #68) and lands as a PR from `claude/test-placement` into `harness-dist-pipeline`; #68 then goes into `main`.

Current state that shapes the design:

- `plugin_maintenance/render.py` already exports `render_tree(repo_root, harness, output_dir)`, the `Harness` Literal, `HARNESS_MANIFESTS`, and `DIST_DIRS`. `plugin_maintenance/build.py` already renders both trees into a temp dir inside `stale_paths()`. `plugin_maintenance/__init__.py` holds only `REPO_ROOT`.
- `tests/` holds 18 flat modules. Seven read `SKILL.md.j2`. Five spell the authored tree as `REPO_ROOT / "plugins"` rather than a `"plugins/..."` literal. Several open with `from conftest import REPO_ROOT`, which works only because `tests/conftest.py` re-exports it by accident.
- `tests/conftest.py` holds `fixture_repo` and `fixture_matrix`, used only by the renderer tests.
- Three test modules live under `plugins/**/tests/` (29 tests). CI never runs them; the renderer copies them into four `dist/**/tests/` directories.
- `pytest.ini` is two lines: `norecursedirs = examples`, `pythonpath = .`. The default `prepend` import mode is in effect.
- Baseline on this branch: `uv run pytest tests -q` gives 236 passed, 7 skipped; `uv run pytest plugins -q` gives 29 passed.
- The CI job is named `gate` and is a required status check.

## Goals / Non-Goals

**Goals:**

- One rule an author can apply without thinking: a test reads the artifact, and only build-layer tests read the source.
- One render mechanism, reached as a plain function through a fixture — no second renderer, no second harness list, no subprocess.
- A layout that says where a new test goes before it is written.
- Two policy checks that make the boundary a test failure rather than a convention.

**Non-Goals:**

- No new renderer behavior, and no `tests/` filter inside the renderer (see D6).
- No evaluation harness and no LLM calls in this change — only the marker and the option a later change will use.
- No change to the CI workflow beyond what a path change would force; the `gate` job name is load-bearing.

## Decisions

### D1. The boundary is "artifact, not source", and the build layer is its one exception

A test reaches plugin content through a fresh render. The single carve-out is `tests/unit/plugin_maintenance/`, whose subject matter *is* the authored tree and the template rules; those tests read `plugins/` and `.j2` because there is nothing else for them to read.

This is what makes the rest of the change mechanical: once the rule is one sentence, every file placement follows from "what does this test read?".

Alternative — allow a rendered-content test to fall back to the template when the rendered file is inconvenient: rejected. That is precisely the state commit `8c987e1` produced, and the convenience is illusory, because an assertion on `{{ actions.AskUser | call }}` passes on a template that never renders.

### D2. Layout: mirror the source tree, per the repo's own convention

`plugins/python-dev-workflow/skills/tests-manager/references/test-structure.md` is this repository's published rule for other people's projects; it applies here.

```text
tests/
  conftest.py                          harness / rendered fixtures, markers, options
  unit/
    plugin_maintenance/                the build layer - the only reader of the authored tree
      conftest.py                      fixture_repo, fixture_matrix
      generators/
    plugins/<plugin>/skills/<skill>/   tests of skill scripts, read through `rendered`
  integration/
    rendered/                          assertions on rendered content
    repo/                              repository conventions that read no plugin content
```

Directories are created only as a test needs them.

`tests/integration/repo/` is a refinement of the placement list, not of the boundary rule. Two existing modules assert repository conventions and touch no plugin content: `test_agents_imports.py` (every `AGENTS.md` has a `CLAUDE.md` beside it) and `test_readme_plugin_catalog.py` (the README kanban lists every catalogued plugin). Filing them under `rendered/` would name them after a tree they never open. One extra directory is cheaper than two misfiled modules.

Final placement:

| Now | After |
|---|---|
| `tests/test_harness_renderer.py` | `tests/unit/plugin_maintenance/test_render.py` |
| `tests/test_harness_action_matrix.py` | `tests/unit/plugin_maintenance/test_harness_action_matrix.py` |
| `tests/test_harness_frontmatter_matrix.py` | `tests/unit/plugin_maintenance/test_harness_frontmatter_matrix.py` |
| `tests/test_template_source_policy.py` | `tests/unit/plugin_maintenance/test_template_source_policy.py` plus the two new policy checks |
| `tests/test_ci_gate.py` | `tests/unit/plugin_maintenance/test_ci_gate.py` |
| `tests/test_dist_invariants.py`, freshness and byte-identical rebuild | `tests/unit/plugin_maintenance/test_build.py` |
| `tests/test_dist_invariants.py`, everything else | `tests/integration/rendered/test_invariants.py` |
| `tests/test_mermaid_diagrams_plugin.py`, generator half | `tests/unit/plugin_maintenance/generators/test_mermaid_diagrams.py` |
| `tests/test_mermaid_diagrams_plugin.py`, skill-content half | `tests/integration/rendered/mermaid_diagrams/test_skill_content.py` |
| `tests/test_dist_publication.py` | `tests/integration/rendered/test_publication.py` |
| `tests/test_ai_assistant_harness_adaptation_skill.py` | `tests/integration/rendered/ai_assistant_ops/test_adapt_skill_for_ai_harness.py` |
| `tests/test_improve_skill.py` | `tests/integration/rendered/ai_assistant_ops/test_improve_skill.py` |
| `tests/test_python_dev_workflow_plugin.py` | `tests/integration/rendered/python_dev_workflow/test_plugin.py` |
| `tests/test_job_hunt_workspace_layout.py` | `tests/integration/rendered/job_hunt_toolkit/test_workspace_layout.py` |
| `tests/test_resume_tailoring.py` | `tests/integration/rendered/job_hunt_toolkit/test_resume_tailoring.py` |
| `tests/test_interview_decision_log.py`, skill-content half | `tests/integration/rendered/work_session_tools/test_interview.py` |
| `tests/test_interview_decision_log.py`, script half | `tests/unit/plugins/work-session-tools/skills/interview/test_decision_log.py` |
| `tests/test_typst_export_script.py` | `tests/unit/plugins/job-hunt-toolkit/skills/export-pdf/test_typst_to_pdf.py` |
| `tests/test_agents_imports.py` | `tests/integration/repo/test_agents_imports.py` |
| `tests/test_readme_plugin_catalog.py` | `tests/integration/repo/test_readme_plugin_catalog.py` |
| md-bloat-hunter's own `tests/test_scripts.py` | `tests/unit/plugins/ai-assistant-ops/skills/md-bloat-hunter/test_scripts.py` |
| md-bloat-hunter's own `tests/test_schemas.py` | `tests/unit/plugins/ai-assistant-ops/skills/md-bloat-hunter/test_schemas.py` |
| version-bumper's own `tests/test_find_versions.py` | `tests/unit/plugins/dev-workflow/skills/version-bumper/test_find_versions.py` |

### D3. `HARNESSES` is derived, and the package root is where it goes

```python
from plugin_maintenance.render import HARNESS_MANIFESTS
HARNESSES = tuple(HARNESS_MANIFESTS)
```

Three harness-keyed structures already exist (`Harness`, `HARNESS_MANIFESTS`, `DIST_DIRS`); the test suite must not become a fourth. `HARNESS_MANIFESTS` is the right parent because manifest membership is what makes a harness real — a harness with no manifest renders nothing.

`render.py` imports nothing from its own package, so the package importing it is not a cycle. The cost is that importing `plugin_maintenance` now pulls `jinja2` and `pathspec`; both are project dependencies rather than dev extras, so nothing that imports the package could have run without them anyway.

Alternative — move `HARNESS_MANIFESTS`, `DIST_DIRS` and `Harness` up into the package root and have `render.py` import down: a cleaner dependency direction, rejected as a wider diff for no behavioral gain.

A one-line assertion in the matrix schema test keeps `HARNESSES` and the `Harness` Literal from drifting apart.

### D4. `harness` is a session-scoped parametrized fixture, and `rendered` depends on it

```python
@pytest.fixture(scope="session", params=HARNESSES)
def harness(request): ...

@pytest.fixture(scope="session")
def rendered(harness, tmp_path_factory): ...   # render_tree(REPO_ROOT, harness, tree)
```

`rendered` must be session-scoped so the tree is rendered once per harness rather than once per test, and pytest forbids a session-scoped fixture depending on a narrower one — so `harness` is session-scoped too. Parametrizing a session-scoped fixture yields one cached instance per harness, which is exactly the shape wanted.

Narrowing happens in `pytest_generate_tests`: when a test requests `harness`, the list starts as `HARNESSES`, is cut to one entry by `@pytest.mark.harness("<name>")`, is intersected with `--harness <name>`, and is applied with `metafunc.parametrize(..., indirect=True, scope="session")`. A test whose marker names a harness the option excludes ends up with an empty parameter set and is reported skipped, which is the honest outcome: the run was asked not to cover that harness.

Alternative — `pytest_collection_modifyitems` deselecting by marker: rejected; it cannot narrow the parametrization itself, so the other harness's tree would still be rendered.

Alternative — a subprocess call to `python -m plugin_maintenance.render`: rejected. `render_tree` is a plain function; calling it directly gives real exceptions and a real traceback, and the parent change already made one renderer the whole mechanism.

Stage 1 (generators) is deliberately not run by the fixture: it writes into `plugins/`, which a test run must not do, and the CI gate runs the full build before `pytest`.

### D5. Template-syntax assertions are deleted, not relocated

Every assertion that names template syntax in a rendered-content test goes. The harness-format guarantee is already carried by three checks that survive: the matrix-derived foreign-name scan, the leftover-marker scan, and byte-identical consecutive builds. An assertion that a template contains `{{ actions.AskUser | call }}` adds nothing to those three and passes on a template that fails to render.

Two consequences worth naming:

- `test_resume_tailoring.py`'s template-syntax assertion is really the claim "this skill asks the user before proceeding". That is prompt behavior; checking it needs a model, so it is deleted here and belongs to a future `llm`-marked evaluation. Recorded as a non-goal so it is not mistaken for an oversight.
- `test_python_dev_workflow_plugin.py` currently resolves a metadata reference path by falling back to a template name when the plain file is missing. Against `rendered` the fallback disappears: the path either resolves in the tree the user installs or it does not, which is the claim worth making.

### D6. The `tests/` rule is enforced at the source, not in the renderer

The renderer gains no `tests/` skip. Adding one would make a re-added skill-local test directory silently vanish from the published tree while still sitting in the authored one, unrun by CI — the same class of invisibility this change exists to remove. Instead a source-policy check asserts that no `tests/` directory exists under the authored plugin tree, so a re-add is a named failure.

This is also why the `harness-dist-build` delta is an ADDED requirement rather than a modification of "Development files excluded": that requirement describes a renderer filter keyed on the emitted name, and this rule is not one.

### D7. The policy check matches both spellings of the authored tree

The check scans every file under `tests/` except `tests/unit/plugin_maintenance/**` and the root `tests/conftest.py`, and fails on a template suffix or on a path into the authored tree.

Such a path has two spellings in this repository: the slash-bearing literal, and the quoted path segment joined onto `REPO_ROOT`. Five current test modules use the second. Matching only the first would leave the exact files this change is fixing free to come back, so the check matches both and nothing else — a bare unquoted word stays legal, because prose and identifiers use it constantly.

### D8. Publication tests assert the manifest, and membership against `rendered`

`test_dist_publication.py` today asserts both the shape of each manifest `source` string and that the directory it names exists under the committed tree. The string assertion stays: it reads the manifest, which is repository configuration rather than a build artifact. The directory-existence assertion becomes a membership assertion against `rendered` — the plugin the manifest lists is present in that harness's rendered tree. Whether the *committed* tree is current is exactly what the freshness check answers, and duplicating it here would be the "test the source and the artifact" double-run the boundary rule forbids.

### D9. `--import-mode=importlib` instead of `__init__.py` scaffolding

A mirrored tree repeats basenames (`test_scripts.py`, `test_schemas.py`, and more as it grows). Under the default `prepend` import mode, two same-named test modules without packages collide at import. The two fixes are a chain of empty `__init__.py` files down every mirrored directory, or one line in `pytest.ini`. One line wins.

The same edit registers both markers:

```ini
[pytest]
norecursedirs = examples
pythonpath = .
addopts = --import-mode=importlib
markers =
    harness(name): run this test only for the named harness
    llm: calls an LLM; skipped unless --llm is given
```

`pythonpath = .` stays, so `plugin_maintenance` imports as before. The `from conftest import REPO_ROOT` idiom disappears with the move: tests import `REPO_ROOT` from `plugin_maintenance`, where it is actually defined.

### D10. CI is untouched

`.github/workflows/ci.yml` already runs the full build, stages and diffs the whole tree, and runs `uv run pytest tests`. With every test now under `tests/`, that one command covers the whole suite — including the 29 tests CI has never run — and `llm` tests skip by default. No step changes, and in particular the job name `gate` does not, because it is a required status check.

## Risks / Trade-offs

- [A mass move plus edits can quietly drop a test] → the verification task compares counts explicitly: the suite must collect at least 265 tests (236 + 29), and the authored plugin tree must collect zero.
- [`rendered` adds a render to session startup] → measured: a full both-tree render runs in well under a second, and the session scope pays it once per harness. The current suite already renders both trees four times inside its 3.4s.
- [Rendered-content tests get slower to write, because a path now goes through a fixture] → accepted; that friction is the boundary doing its job.
- [Deleting the resume-tailoring prompt assertion leaves a real behavior unchecked until the eval exists] → recorded as a non-goal rather than replaced by a weaker text assertion; a substring check on a template was never coverage of it.
- [`--import-mode=importlib` changes how test modules import each other] → no test module imports another after the move; the one cross-module import is removed in the same pass.
- [A narrowed run reports skips that can read as failures] → the empty parameter set is pytest's own reporting; the option is a local convenience and CI never passes it.

## Migration Plan

One PR from `claude/test-placement` into `harness-dist-pipeline`. Order inside it is test-first in the sense the parent change established: the guard lands before the thing it guards.

1. `HARNESSES`, the `tests/conftest.py` fixtures, markers and options, and `pytest.ini` — the mechanism, proven by moving one file onto it.
2. The two policy checks, which fail loudly against the unmoved tree and define "done" for the next step.
3. The moves and rewrites, group by group, until both policy checks pass.
4. Delete the skill-local test directories, rebuild the published trees, bump the two affected plugins, update `AGENTS.md` and the md-bloat-hunter sentence.
5. Full verification: build, `pytest tests`, JSON validation, `git diff --check`.

Rollback: revert the PR. The skill-local tests, the published trees, and the flat `tests/` tree return together.
