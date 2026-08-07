# Tasks: harness-dist-pipeline

The whole change lands in one PR. Development is test-first (TDD): each behavior's failing tests land before its implementation; the suite is fully green only at the end. Test tasks are authored with the repo's `python-dev-workflow:tests-manager` skill.

## 1. Build foundation

- [ ] 1.1 Add Jinja2 to the root `pyproject.toml` dev dependency-group and lock with `uv`
- [ ] 1.2 Write failing renderer unit tests on a fixture plugin: `actions.*` resolution, both wrapper name shapes, narrative conditional, collision failure, missing-action failure, unknown-harness failure, dev-file exclusion, mode-bit preservation, manifest-driven membership
- [ ] 1.3 Write the failing matrix schema test (`callable` flag on every action; one name per callable action per assistant; single wrapper per assistant)
- [ ] 1.4 Create the root `plugin_maintenance/` package with the stage-1 runner (iterates `generators/*` packages, calls each zero-argument `generate()`)
- [ ] 1.5 Implement the stage-2 renderer against the 1.2 tests: harness argument, matrix loading, resolved `actions` map, wrapper filter for bare and qualified names, `StrictUndefined`
- [ ] 1.6 Implement the file rules: plain files copied byte-for-byte with mode bits preserved; `*.j2` rendered with the suffix stripped; `X`+`X.j2` collision fails the build; files named `AGENTS.md`/`CLAUDE.md`/`README.md` never emitted; each tree contains exactly the plugins its marketplace manifest lists
- [ ] 1.7 Implement foreign-runtime-metadata stripping (`.codex-plugin/` out of the Claude Code tree, `.claude-plugin/` out of the Codex tree)
- [ ] 1.8 Implement fail-loud checks: unknown harness, missing action/name, malformed matrix, render error, leftover Jinja markers in rendered files (`{% raw %}` output exempt), plain/template collision
- [ ] 1.9 Update `harness-action-matrix.json` to the D3 schema: `callable` flag on every action; one `name` per assistant for callable actions; task tracking split into `CreateTask`/`GetTask`/`ListTasks`/`UpdateTask`/`StopTask` (all → `update_plan` on Codex); `PluginManifest`/`SlashCommand` non-callable; `InvokeSkill`, `surface`, and `terms` dropped; keep `lookup_order`; refresh `checked`; 1.3 goes green

## 2. Mermaid generator relocation

- [ ] 2.1 Update `tests/test_mermaid_diagrams_plugin.py` expectations first: root-project invocations, relocated generator paths, dist-pointing manifest sources
- [ ] 2.2 Move `plugins/mermaid-diagrams/plugin_maintenance/` to `plugin_maintenance/generators/mermaid_diagrams/` (offline `generate()`; the upstream fetch stays a separate weekly updater outside the build); dissolve its standalone `pyproject.toml` and `uv.lock` into the root project
- [ ] 2.3 Update generator internals/paths so generated docs keep landing under `plugins/mermaid-diagrams/`; 2.1 goes green except the manifest assertions (green at 5.2)

## 3. Dist invariant tests

- [ ] 3.1 Write dist purity tests: matrix-derived foreign-name scan on `.j2`-rendered files (exemption list honored), no leftover markers in rendered files (`{% raw %}` output exempt), no `*.j2` in dist, no legacy dispatch artifacts, metadata stripping, no dev files (`AGENTS.md`/`CLAUDE.md`/`README.md`)
- [ ] 3.2 Write template-source policy tests: no literal matrix-mapped callable names in `.j2` sources, no callable names selected inside harness conditionals, no `X`+`X.j2` collisions repo-wide
- [ ] 3.3 Write publication tests: every manifest entry points into its own `dist/` tree and resolves; catalogs may diverge (Codex-only `run-and-verify-app`)
- [ ] 3.4 Write the reproducibility test: two consecutive full builds are byte-identical

## 4. Migration

- [ ] 4.1 Convert the pilot skill `dev-workflow/skills/commit` to `SKILL.md.j2`: fold its harness reference files inline, delete them, remove the dispatch sentence and metadata links; run the full build and verify the pilot renders correctly in both trees
- [ ] 4.2 Convert the remaining 27 dispatch-sentence skills (29 carriers minus the pilot and minus `adapt-skill-for-ai-harness`, which group 6 rewrites): fold reference files inline; delete all 55 `references/ai-assistant-harnesses/` files — 50 top-level plus 5 under langfuse's nested sub-skills (`create-dataset` has only `claude-code.md`) — plus dispatch sentences and metadata links; wrap the literal `{{ }}` content in `job-hunt-toolkit`'s `new-application` and `prepare-to-send` in `{% raw %}` during conversion
- [ ] 4.3 Sweep `references/**/*.md` (recursive; includes nested sub-skill trees) for harness-specific wording; convert those files to `.j2` where found
- [ ] 4.4 Delete `tests/test_harness_reference_policy.py` once its ported invariants pass

## 5. Publication and CI

- [ ] 5.1 Run the full build; commit both complete `dist/` trees; group 3 tests all green
- [ ] 5.2 Repoint `.claude-plugin/marketplace.json` to `./dist/claude-code/<name>` and `.agents/plugins/marketplace.json` to `./dist/codex/<name>` for every plugin each manifest lists
- [ ] 5.3 Verify a local marketplace install of the pilot plugin from each harness's manifest
- [ ] 5.4 Add the PR-gate workflow: full build + `git diff --exit-code` over the whole tree + `uv run pytest tests`
- [ ] 5.5 Rework `sync-mermaid-docs.yml`: fetch the upstream snapshot, delete the temporary checkout, run the full build, open a PR with the combined `plugins/` + `dist/` changes (no direct pushes); delete the old PR-validation job — the gate covers it

## 6. Adaptation skill greenfield rewrite

- [ ] 6.1 Rewrite `tests/test_ai_assistant_harness_adaptation_skill.py` first against the new skill contract (template authoring, matrix schema per D3)
- [ ] 6.2 Rewrite the `adapt-skill-for-ai-harness` skill from scratch — every file in the skill directory (`SKILL.md`, `references/` including `live-lab-protocol.md`, `scripts/lookup_harness_action.py`, `evals/`, `README.md`): template-model authoring and matrix contract only; delete files with no greenfield replacement; no legacy pattern, migration notes, or history anywhere; 6.1 goes green

## 7. Docs and versions

- [ ] 7.1 Update `AGENTS.md`: two-stage build workflow, `plugin_maintenance/` layout, "author in `plugins/`, never edit `dist/`", build commands
- [ ] 7.2 Update `README.md`: development workflow and catalog wording reflect `dist/` as the installed source
- [ ] 7.3 Minor-bump every plugin's version in both runtime `plugin.json` manifests (all plugins ship re-rendered content in this change)
- [ ] 7.4 Run full verification: JSON validation, `git diff --check`, `uv run pytest tests`
