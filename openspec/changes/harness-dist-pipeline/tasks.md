# Tasks: harness-dist-pipeline

## 1. Build foundation

- [ ] 1.1 Add Jinja2 to the root `pyproject.toml` dev dependency-group and lock with `uv`
- [ ] 1.2 Create the root `plugin_maintenance/` package with the stage-1 runner (iterates generator subdirectories, runs each declared entrypoint)
- [ ] 1.3 Implement the stage-2 renderer: harness argument, matrix loading, resolved `actions` map, wrapper filter for bare and qualified names, `StrictUndefined`
- [ ] 1.4 Implement the file rules in the renderer: copy plain files byte-for-byte, render `*.j2` with suffix stripped, fail on `X`+`X.j2` collision
- [ ] 1.5 Implement foreign-runtime-metadata stripping (`.codex-plugin/` out of the Claude Code tree, `.claude-plugin/` out of the Codex tree)
- [ ] 1.6 Implement fail-loud checks: unknown harness, missing action/name, malformed matrix, render error, leftover Jinja markers in rendered files
- [ ] 1.7 Update `harness-action-matrix.json`: per-assistant `name` for mapped actions, one top-level invocation wrapper per assistant, drop nothing else (`lookup_order`, `adaptation`, `surface` stay); refresh `checked`

## 2. Mermaid generator relocation

- [ ] 2.1 Move `plugins/mermaid-diagrams/plugin_maintenance/` into `plugin_maintenance/mermaid-diagrams/` and dissolve its standalone `pyproject.toml` into the root project
- [ ] 2.2 Update generator internals/paths so `generated_docs` and `sync` write into `plugins/mermaid-diagrams/` as before
- [ ] 2.3 Update `tests/test_mermaid_diagrams_plugin.py` imports/paths and verify it passes from the root project

## 3. Pilot render and publication

- [ ] 3.1 Convert one pilot skill (`dev-workflow/skills/commit` or `work-session-tools/skills/interview`) to `SKILL.md.j2`: fold its two harness reference files inline, delete them, remove the dispatch sentence and metadata links
- [ ] 3.2 Run the full build; verify the pilot renders correctly in both trees and every other plugin copies through untouched
- [ ] 3.3 Commit both complete `dist/` trees
- [ ] 3.4 Repoint `.claude-plugin/marketplace.json` to `./dist/claude-code/<name>` and `.agents/plugins/marketplace.json` to `./dist/codex/<name>` for every plugin (same PR as 3.3)
- [ ] 3.5 Verify a local marketplace install of the pilot plugin from each harness's manifest

## 4. Tests

- [ ] 4.1 Renderer unit tests on a fixture plugin: `actions.*` resolution, both wrapper name shapes, narrative conditional, collision failure, missing-action failure, unknown-harness failure
- [ ] 4.2 Dist purity tests: per-tree foreign-vocabulary scan (ported lists), no leftover markers in rendered files, no `*.j2` in dist, no legacy dispatch artifacts, metadata stripping
- [ ] 4.3 Template-source policy tests: no literal matrix-mapped callable names in `.j2` sources, no callable names selected inside harness conditionals, no `X`+`X.j2` collisions repo-wide
- [ ] 4.4 Publication tests: every manifest source path points into its own `dist/` tree and resolves; matrix schema test (name per mapped action per assistant, single wrapper per assistant)
- [ ] 4.5 Reproducibility test: two consecutive full builds are byte-identical
- [ ] 4.6 Delete `tests/test_harness_reference_policy.py` once its ported invariants pass

## 5. CI

- [ ] 5.1 Add the PR-gate workflow: stage 1 + stage 2 + `git diff --exit-code -- plugins/ dist/` + `uv run pytest tests`
- [ ] 5.2 Update `sync-mermaid-docs.yml`: root-project invocations, stage-2 render after sync, `file_pattern` widened to include `dist/`; fold or keep the old PR-validation job per D6

## 6. Batch migration

- [ ] 6.1 Convert the remaining ~28 dispatch-sentence skills to `.j2`: fold reference files inline, delete `references/ai-assistant-harnesses/` dirs, dispatch sentences, and metadata links
- [ ] 6.2 Sweep `references/*.md` for harness-specific wording; convert those files to `.j2` where found
- [ ] 6.3 Re-render, commit updated `dist/`, confirm all purity and policy tests pass

## 7. Adaptation skill rewrite

- [ ] 7.1 Rewrite `adapt-skill-for-ai-harness` SKILL.md greenfield for the template model (authoring guidance, matrix contract, no legacy mentions)
- [ ] 7.2 Rewrite `tests/test_ai_assistant_harness_adaptation_skill.py` against the new content; update the skill's evals if present

## 8. Docs and versions

- [ ] 8.1 Update `AGENTS.md`: two-stage build workflow, `plugin_maintenance/` layout, "author in `plugins/`, never edit `dist/`", build commands
- [ ] 8.2 Update `README.md`: development workflow and catalog wording reflect `dist/` as the installed source
- [ ] 8.3 Bump versions for every plugin whose distributed content changed, plus marketplace metadata, per repo convention
- [ ] 8.4 Run full verification: JSON validation, `git diff --check`, `uv run pytest tests`
