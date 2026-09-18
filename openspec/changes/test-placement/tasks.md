# Tasks: test-placement

Everything lands in one PR from `claude/test-placement` into `harness-dist-pipeline`. Order is guard-first: the mechanism, then the policy checks that fail against the unmoved tree, then the moves that turn them green. Each group leaves the suite runnable.

## 1. Mechanism

- [x] 1.1 Add `HARNESSES = tuple(HARNESS_MANIFESTS)` to `plugin_maintenance/__init__.py`, importing `HARNESS_MANIFESTS` from `plugin_maintenance.render`; add no second list of harness names anywhere
- [x] 1.2 Assert in the action-matrix schema test that `HARNESSES` and the `Harness` Literal name the same harnesses, so the two cannot drift
- [x] 1.3 Rewrite `tests/conftest.py` to hold only the shared mechanism: `pytest_addoption` for `--harness` and `--llm`, a session-scoped `harness` fixture parametrized over `HARNESSES`, a session-scoped `rendered` fixture calling `render_tree(REPO_ROOT, harness, <tmp tree>)`, and the `llm` skip in `pytest_collection_modifyitems`
- [x] 1.4 Implement harness narrowing in `pytest_generate_tests`: start from `HARNESSES`, cut to one entry on `@pytest.mark.harness("<name>")`, intersect with `--harness`, apply with `indirect=True, scope="session"`
- [x] 1.5 Move `fixture_repo` and `fixture_matrix` out of `tests/conftest.py` into a new `tests/unit/plugin_maintenance/conftest.py`
- [x] 1.6 Update `pytest.ini`: keep `norecursedirs` and `pythonpath`, add `addopts = --import-mode=importlib`, register the `harness(name)` and `llm` markers
- [x] 1.7 Prove the mechanism on one file: move `tests/test_improve_skill.py` to `tests/integration/rendered/ai_assistant_ops/test_improve_skill.py`, reading the skill through `rendered`; confirm it runs twice, once per harness

## 2. Policy checks (fail first)

- [x] 2.1 Move `tests/test_template_source_policy.py` to `tests/unit/plugin_maintenance/test_template_source_policy.py` unchanged, replacing `from conftest import REPO_ROOT` with an import from `plugin_maintenance`
- [x] 2.2 Add the test-boundary policy check there: no file under `tests/`, outside `tests/unit/plugin_maintenance/` and the root `tests/conftest.py`, contains a template suffix or a path into the authored plugin tree in either spelling (slash-bearing literal or quoted path segment); the failure names every offending file
- [x] 2.3 Add the centralization policy check there: no directory named `tests/` exists anywhere under the authored plugin tree; the failure names the directory
- [x] 2.4 Confirm both checks fail now, listing the seven template-reading modules and the two skill-local test directories — this is the definition of done for groups 3 to 5

## 3. Build-layer tests

- [x] 3.1 Move `tests/test_harness_renderer.py` to `tests/unit/plugin_maintenance/test_render.py`
- [x] 3.2 Move `tests/test_harness_action_matrix.py` and `tests/test_harness_frontmatter_matrix.py` to `tests/unit/plugin_maintenance/`
- [x] 3.3 Move `tests/test_ci_gate.py` to `tests/unit/plugin_maintenance/test_ci_gate.py`
- [x] 3.4 Split `tests/test_dist_invariants.py`: the freshness check (`stale_paths`) and the byte-identical-rebuild check become `tests/unit/plugin_maintenance/test_build.py`; they keep reading the committed trees, because that is what they are for
- [x] 3.5 Split `tests/test_mermaid_diagrams_plugin.py`: the generator-package assertions become `tests/unit/plugin_maintenance/generators/test_mermaid_diagrams.py`
- [x] 3.6 Replace `from conftest import REPO_ROOT` with `from plugin_maintenance import REPO_ROOT` in every moved module

## 4. Rendered-content tests

- [x] 4.1 Move the remainder of `tests/test_dist_invariants.py` to `tests/integration/rendered/test_invariants.py` and repoint every scan from the committed tree to `rendered`, dropping the per-harness `parametrize` in favour of the `harness` fixture
- [x] 4.2 Move `tests/test_dist_publication.py` to `tests/integration/rendered/test_publication.py`: keep the manifest `source` string assertions, replace directory existence under the committed tree with plugin membership in `rendered`
- [x] 4.3 Move `tests/test_ai_assistant_harness_adaptation_skill.py` to `tests/integration/rendered/ai_assistant_ops/test_adapt_skill_for_ai_harness.py`, reading the skill through `rendered`; keep the assertions whose subject is genuinely the template model, since this skill's content is about templates, and drop any that assert the skill file's own template syntax
- [x] 4.4 Move `tests/test_python_dev_workflow_plugin.py` to `tests/integration/rendered/python_dev_workflow/test_plugin.py`; delete the template-existence assertions and the template fallback in the metadata reference resolution, so a reference path either resolves in the rendered tree or fails
- [x] 4.5 Move `tests/test_job_hunt_workspace_layout.py` to `tests/integration/rendered/job_hunt_toolkit/test_workspace_layout.py`, reading every path through `rendered`
- [x] 4.6 Move `tests/test_resume_tailoring.py` to `tests/integration/rendered/job_hunt_toolkit/test_resume_tailoring.py`, reading through `rendered` and deleting the template-syntax assertion that stood in for "the skill asks the user before proceeding"
- [x] 4.7 Move the skill-content half of `tests/test_interview_decision_log.py` to `tests/integration/rendered/work_session_tools/test_interview.py`, reading the skill through `rendered`
- [x] 4.8 Move the skill-content half of `tests/test_mermaid_diagrams_plugin.py` to `tests/integration/rendered/mermaid_diagrams/test_skill_content.py`, reading through `rendered`
- [x] 4.9 Move `tests/test_agents_imports.py` and `tests/test_readme_plugin_catalog.py` to `tests/integration/repo/`; derive the README catalog's expected plugin list from the marketplace manifest rather than from the authored plugin tree

## 5. Skill-script tests

- [ ] 5.1 Move md-bloat-hunter's `test_scripts.py` and `test_schemas.py` to `tests/unit/plugins/ai-assistant-ops/skills/md-bloat-hunter/`, loading the scripts, schemas and skill file from `rendered`; revert commit `8c987e1`'s template retarget in the process
- [ ] 5.2 Move version-bumper's `test_find_versions.py` to `tests/unit/plugins/dev-workflow/skills/version-bumper/test_find_versions.py`, loading the script from `rendered`
- [ ] 5.3 Move the script half of `tests/test_interview_decision_log.py` to `tests/unit/plugins/work-session-tools/skills/interview/test_decision_log.py`, running the shell script from `rendered` and keeping its executable-bit dependency honest
- [ ] 5.4 Move `tests/test_typst_export_script.py` to `tests/unit/plugins/job-hunt-toolkit/skills/export-pdf/test_typst_to_pdf.py`, running the script from `rendered`; keep the `typst`-missing skip
- [ ] 5.5 Delete `plugins/ai-assistant-ops/skills/md-bloat-hunter/tests/` and `plugins/dev-workflow/skills/version-bumper/tests/`; check 2.3 goes green
- [ ] 5.6 Confirm 2.2 goes green: no file outside the build layer names a template or a path into the authored tree

## 6. Consequences

- [ ] 6.1 Edit `plugins/ai-assistant-ops/skills/md-bloat-hunter/SKILL.md.j2` so the sentence "During normal invocation, `docs/` and `tests/` are skill-dev artifacts only." no longer mentions `tests/`, which the skill no longer has
- [ ] 6.2 Run the full build and commit both published trees, which now carry no `tests/` directories
- [ ] 6.3 Bump `ai-assistant-ops` and `dev-workflow` in both runtime manifests with the repo's `version-bumper` skill, since their shipped trees change; leave every other plugin alone
- [ ] 6.4 Document in `AGENTS.md` (Development Workflow) the test layout, the boundary rule and its one build-layer exception, the `harness` and `rendered` fixtures, the `harness` and `llm` markers, and the `--harness` and `--llm` options
- [ ] 6.5 Confirm `.github/workflows/ci.yml` needs no edit: it already runs the full build, the staged diff, and `uv run pytest tests`; the `gate` job name must not change

## 7. Verification

- [ ] 7.1 `uv run pytest tests -q` collects at least 265 tests (236 previously under `tests/` plus 29 moved in) and passes, with only the pre-existing environment-dependent skips
- [ ] 7.2 `uv run pytest plugins -q` collects zero tests
- [ ] 7.3 `uv run pytest tests -q --harness Codex` runs the harness-independent tests plus the Codex ones and nothing for the other harness; the same for the other harness name
- [ ] 7.4 `uv run pytest tests -q` reports no unknown-marker warning, and an `llm`-marked probe test skips without `--llm` and runs with it
- [ ] 7.5 `uv run python -m plugin_maintenance.build --check` reports the published trees match
- [ ] 7.6 `jq empty .agents/plugins/marketplace.json .claude-plugin/marketplace.json` and `find plugins dist -path '*/plugin.json' -print0 | xargs -0 jq empty` pass
- [ ] 7.7 `git diff --check` is clean
