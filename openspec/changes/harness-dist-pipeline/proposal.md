# Proposal: harness-dist-pipeline

Tracking issue: https://github.com/Alex-Kopylov/zweihander/issues/67 (supersedes PR #65).

## Why

Zweihander authors plugins once but ships them to two harnesses (Claude Code and Codex) whose native interfaces have different names. The current runtime-dispatch pattern — 55 per-harness reference files plus 29 dispatch sentences — makes every skill execution pay a context cost for content that is irrelevant to the executing harness. A skill is edited once or twice but executed 100+ times, so adaptation cost must move from run time to build time.

## What Changes

- Add a two-stage build pipeline:
  - Stage 1 (generation): plugins that generate their own content run their declared build scripts in-place. `mermaid-diagrams` becomes the first member of this general class; nothing hardcodes it.
  - Stage 2 (distribution): one renderer renders `plugins/` into a complete installable tree per harness: `dist/claude-code/` and `dist/codex/`, both committed.
- Add Jinja templating for harness-dependent files: `X.j2` renders to `X`; plain files copy byte-for-byte; `X` and `X.j2` together fail the build.
- Exclude development files from `dist/`: files named `AGENTS.md`, `CLAUDE.md`, or `README.md` under `plugins/` are never emitted into either tree.
- Adopt one uniform invocation notation per harness for every callable in rendered narrative: `Skill(<name>)` for Claude Code, `$<name>` for Codex, with exactly two name shapes (bare `skill-name`, qualified `plugin-name:skill-name`). No tool/skill/surface distinctions.
- Simplify `harness-action-matrix.json`: a `callable` flag per action; callable actions map to one name per harness (task tracking splits into per-operation actions, all mapping to `update_plan` on Codex); the invocation wrapper is stored once per harness; `surface` and the multi-term lists are dropped; PR #65's per-action `invocations` design is not adopted (it was never merged).
- **BREAKING**: both root marketplace manifests repoint plugin sources from `./plugins/<name>` to `./dist/claude-code/<name>` / `./dist/codex/<name>`. Each manifest stays the catalog authority for its harness; the two catalogs may list different plugin sets (`run-and-verify-app` is Codex-only).
- Remove the runtime-dispatch pattern: `references/ai-assistant-harnesses/*.md` files, dispatch sentences, and `metadata.ai-assistant-harness-adaptation.<harness>` links; their content folds inline into `.j2` templates. Other `references/` files change only where they carry harness-specific wording (swept and templated in the same pass).
- Treat skill frontmatter as the portability boundary: an `allowed-tools` grant is declared once through a renderer global and lands at the top level for Claude Code and under `metadata` for Codex, a hand-written `metadata:` block merges with it instead of duplicating the key, and every `metadata` block groups its entries one level deep by kind.
- Rewrite `adapt-skill-for-ai-harness` greenfield — every file in the skill directory — for the template model, with no mention of the legacy pattern.
- Relocate build code into a root-level maintenance directory (shared renderer + per-plugin generators, including the relocated mermaid generator); add Jinja2 as a root dev dependency.
- Port harness-policy tests to dist-level invariants; add CI freshness gates; extend the mermaid sync workflow to re-render `dist/`.

## Capabilities

### New Capabilities

- `harness-dist-build`: the two-stage build pipeline — generated-plugin class, per-harness rendering, `X`/`X.j2` file rules, foreign-metadata stripping, failure policy, output invariants (no foreign vocabulary, no leftover Jinja markers, reproducible renders).
- `harness-invocation-notation`: the uniform per-harness invocation notation, the two name shapes, the action→name matrix schema, and the template contract (`actions` lookups, wrapper filter, narrative conditionals only for divergent prose).
- `dist-publication`: committed `dist/` trees, marketplace manifests pointing at them, CI freshness enforcement, and the mermaid sync workflow keeping `dist/` current.
- `harness-adaptation-skill`: what the rewritten `adapt-skill-for-ai-harness` skill must instruct — authoring harness-parametric templates against the matrix — and what it must not contain (legacy reference-file pattern, dispatch sentences, migration notes).

### Modified Capabilities

None — `openspec/specs/` does not exist yet; all capabilities are introduced by this change.

## Impact

- Repo layout: new committed `dist/` trees (repo size roughly triples for plugin content — accepted); new root maintenance directory; `plugins/mermaid-diagrams/plugin_maintenance/` moves out of the plugin.
- Manifests: `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` (source paths), per-plugin `plugin.json` untouched in source but filtered per tree in `dist/`.
- Skills content: 28 `SKILL.md` files become `SKILL.md.j2` (the 29th dispatch-sentence carrier, `adapt-skill-for-ai-harness`, is rewritten greenfield instead); all 55 harness reference files deleted; harness-specific `references/*.md` may become `.j2`; `AGENTS.md`/`CLAUDE.md`/`README.md` stay authoring-only.
- Tests: `tests/test_harness_reference_policy.py` retired/replaced; `tests/test_ai_assistant_harness_adaptation_skill.py` reworked; new renderer and dist-invariant tests.
- CI: `.github/workflows/sync-mermaid-docs.yml` gains a render step and wider commit pattern; new freshness gate.
- Dependencies: Jinja2 in the root `pyproject.toml` dev group (build-time only, never a plugin runtime dependency).
- Docs: `README.md` (development workflow + catalog wording), `AGENTS.md`; version bumps for affected plugins and marketplace metadata.
