# Tasks: harness-dist-pipeline

The whole change lands in one PR. Development is test-first (TDD): each behavior's failing tests land before its implementation; the suite is fully green only at the end. Test tasks are authored with the repo's `python-dev-workflow:tests-manager` skill.

## 1. Build foundation

- [x] 1.1 Add Jinja2 to the root `pyproject.toml` dev dependency-group and lock with `uv`
- [x] 1.2 Write failing renderer unit tests on a fixture plugin: `actions.*` resolution, both wrapper name shapes, narrative conditional, collision failure, missing-action failure, unknown-harness failure, dev-file exclusion, mode-bit preservation, manifest-driven membership
- [x] 1.3 Write the failing matrix schema test (`callable` flag on every action; one name per callable action per assistant; single wrapper per assistant)
- [x] 1.4 Create the root `plugin_maintenance/` package with the stage-1 runner (iterates `generators/*` packages, calls each zero-argument `generate()`)
- [x] 1.5 Implement the stage-2 renderer against the 1.2 tests: harness argument, matrix loading, resolved `actions` map, wrapper filter for bare and qualified names, `StrictUndefined`
- [x] 1.6 Implement the file rules: plain files copied byte-for-byte with mode bits preserved; `*.j2` rendered with the suffix stripped; `X`+`X.j2` collision fails the build; files named `AGENTS.md`/`CLAUDE.md`/`README.md` never emitted; each tree contains exactly the plugins its marketplace manifest lists
- [x] 1.7 Implement foreign-runtime-metadata stripping (`.codex-plugin/` out of the Claude Code tree, `.claude-plugin/` out of the Codex tree)
- [x] 1.8 Implement fail-loud checks: unknown harness, missing action/name, malformed matrix, render error, leftover Jinja markers in rendered files (`{% raw %}` output exempt), plain/template collision
- [x] 1.9 Update `harness-action-matrix.json` to the D3 schema: `callable` flag on every action; one `name` per assistant for callable actions; task tracking split into `CreateTask`/`GetTask`/`ListTasks`/`UpdateTask`/`StopTask` (all → `update_plan` on Codex); `PluginManifest`/`SlashCommand` non-callable; `InvokeSkill`, `surface`, and `terms` dropped; keep `lookup_order`; refresh `checked`; 1.3 goes green

## 2. Mermaid generator relocation

- [x] 2.1 Update `tests/test_mermaid_diagrams_plugin.py` expectations first: root-project invocations, relocated generator paths, dist-pointing manifest sources
- [x] 2.2 Move `plugins/mermaid-diagrams/plugin_maintenance/` to `plugin_maintenance/generators/mermaid_diagrams/` (offline `generate()`; the upstream fetch stays a separate weekly updater outside the build); dissolve its standalone `pyproject.toml` and `uv.lock` into the root project
- [x] 2.3 Update generator internals/paths so generated docs keep landing under `plugins/mermaid-diagrams/`; 2.1 goes green except the manifest assertions (green at 5.2)

## 3. Dist invariant tests

- [x] 3.1 Write dist purity tests: matrix-derived foreign-name scan on `.j2`-rendered files (exemption list honored), no leftover markers in rendered files (`{% raw %}` output exempt), no `*.j2` in dist, no legacy dispatch artifacts, metadata stripping, no dev files (`AGENTS.md`/`CLAUDE.md`/`README.md`)
- [x] 3.2 Write template-source policy tests: no literal matrix-mapped callable names in `.j2` sources, no callable names selected inside harness conditionals, no `X`+`X.j2` collisions repo-wide
- [x] 3.3 Write publication tests: every manifest entry points into its own `dist/` tree and resolves; catalogs may diverge (Codex-only `run-and-verify-app`)
- [x] 3.4 Write the reproducibility test: two consecutive full builds are byte-identical

## 4. Migration

- [x] 4.1 Convert the pilot skill `dev-workflow/skills/commit` to `SKILL.md.j2`: fold its harness reference files inline, delete them, remove the dispatch sentence and metadata links; run the full build and verify the pilot renders correctly in both trees
- [x] 4.2 Convert the remaining 27 dispatch-sentence skills (29 carriers minus the pilot and minus `adapt-skill-for-ai-harness`, which group 6 rewrites): fold reference files inline; delete all 55 `references/ai-assistant-harnesses/` files — 50 top-level plus 5 under langfuse's nested sub-skills (`create-dataset` has only `claude-code.md`) — plus dispatch sentences and metadata links; wrap the literal `{{ }}` content in `job-hunt-toolkit`'s `new-application` and `prepare-to-send` in `{% raw %}` during conversion
- [x] 4.3 Sweep `references/**/*.md` (recursive; includes nested sub-skill trees) for harness-specific wording; convert those files to `.j2` where found
- [x] 4.4 Delete `tests/test_harness_reference_policy.py` once its ported invariants pass

## 5. Publication and CI

- [x] 5.1 Run the full build; commit both complete `dist/` trees; group 3 tests all green
- [x] 5.2 Repoint `.claude-plugin/marketplace.json` to `./dist/claude-code/<name>` and `.agents/plugins/marketplace.json` to `./dist/codex/<name>` for every plugin each manifest lists
- [x] 5.3 Verify a local marketplace install of the pilot plugin from each harness's manifest
- [x] 5.4 Add the PR-gate workflow: full build + `git diff --exit-code` over the whole tree + `uv run pytest tests`
- [x] 5.5 Rework `sync-mermaid-docs.yml`: fetch the upstream snapshot, delete the temporary checkout, run the full build, open a PR with the combined `plugins/` + `dist/` changes (no direct pushes); delete the old PR-validation job — the gate covers it

## 6. Adaptation skill greenfield rewrite

- [x] 6.1 Rewrite `tests/test_ai_assistant_harness_adaptation_skill.py` first against the new skill contract (template authoring, matrix schema per D3)
- [x] 6.2 Rewrite the `adapt-skill-for-ai-harness` skill from scratch — every file in the skill directory (`SKILL.md`, `references/` including `live-lab-protocol.md`, `scripts/lookup_harness_action.py`, `evals/`, `README.md`): template-model authoring and matrix contract only; delete files with no greenfield replacement; no legacy pattern, migration notes, or history anywhere; 6.1 goes green

## 7. Docs and versions

- [x] 7.1 Update `AGENTS.md`: two-stage build workflow, `plugin_maintenance/` layout, "author in `plugins/`, never edit `dist/`", build commands
- [x] 7.2 Update `README.md`: development workflow and catalog wording reflect `dist/` as the installed source
- [x] 7.3 Minor-bump every plugin's version in both runtime `plugin.json` manifests (all plugins ship re-rendered content in this change)
- [x] 7.4 Run full verification: JSON validation, `git diff --check`, `uv run pytest tests`

## 8. Review findings with a recorded author decision

- [x] 8.1 Move plugin-level runtime context into files the renderer emits: `plugins/langfuse/AGENTS.md` becomes `references/langfuse_domain_knowledge.md` with the skill link repointed; `job-hunt-toolkit`'s `AGENTS.md`/`CLAUDE.md` fold into its `references/` and `init-workspace/SKILL.md.j2`; document the rule in root `AGENTS.md`
- [x] 8.2 Test the dev-file rule against the emitted name, not the source name, and fail the build on a dev-file template instead of skipping it
- [x] 8.3 Skip every source path the root `.gitignore` matches, so `__pycache__/` and friends stay out of `dist/`
- [x] 8.4 Give the staging directory the mode of `dist/` before the rename, and replace a plain file sitting at the output path instead of raising
- [x] 8.5 Detect `{% raw %}` blocks with a regex covering every Jinja spelling, and exempt each block's own output instead of the whole file — in the renderer and in `tests/test_dist_invariants.py`
- [x] 8.6 Fold 8.1–8.5 into the delta specs and design decisions, so the archived change records the shipped build contract

## 9. Frontmatter portability boundary

- [x] 9.1 Write failing renderer tests for the frontmatter boundary: top-level `allowed-tools` for Claude Code, `metadata` sub-key for Codex, string and list arguments, empty argument emits nothing, unquotable value fails, hand-written `metadata:` merges into one block, single-block file unchanged, duplicate of another key fails
- [x] 9.2 Implement the `allowed_tools` template global and the frontmatter merge and duplicate-key checks in the renderer, with a `Harness` literal type replacing the bare `harness: str` annotations
- [x] 9.3 Write the source policy test: no hand-written `allowed-tools:` in any skill or agent frontmatter, and every frontmatter `metadata` entry under a declared namespace
- [x] 9.4 Write the dist invariant test: no top-level `allowed-tools` under `dist/codex/**`, and exactly one `metadata:` key per rendered file
- [x] 9.5 Convert the seven existing `metadata:` blocks to the namespaced shape, update the skill and agent bodies that describe them as a routing table, and update `tests/test_python_dev_workflow_plugin.py` to the nested keys
- [x] 9.6 Document the boundary in `adapt-skill-for-ai-harness` and extend `tests/test_ai_assistant_harness_adaptation_skill.py` to cover it
- [x] 9.7 Rebuild both trees and run full verification: `uv run pytest tests`, JSON validation, `git diff --check`

## 10. Argument frontmatter and the interview decision log

- [x] 10.1 Add the frontmatter matrix beside the action matrix, declaring one form and one placement per assistant for every frontmatter key, with its own schema test and a key-then-assistant lookup script
- [x] 10.1a Drive the renderer from it: one global per placed key, three value forms, a validating loader, and renderer tests for placement, quoting, list joining, empty value, a flipped placement, and each failure mode
- [x] 10.1b Sweep every hand-written `argument-hint:` onto the global, renaming the four plain sources that carried one
- [x] 10.2 Add the `config` metadata namespace for a skill's own runtime defaults, in the source policy test and the specs
- [x] 10.3 Exempt a declared argument name from the `$name`-in-a-conditional policy check, with unit tests for the narrow exemption
- [x] 10.4 Give the interview skill a `scripts/decision_log.py` that owns both the append-only log and the progress bar, with tests under `tests/`
- [x] 10.5 Rewrite `interview/SKILL.md.j2`: group questions before the walk, record every decision to the log, review the log, execute only after approval, delegate non-blocking work
- [x] 10.6 Rewrite the frontmatter section of `adapt-skill-for-ai-harness` around the matrix, its forms, its contract, and the lookup script
- [x] 10.7 Rebuild both trees and run full verification: `uv run pytest tests`, JSON validation, `git diff --check`
