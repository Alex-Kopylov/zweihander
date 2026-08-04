# Design: harness-dist-pipeline

## Context

See `proposal.md` for motivation and the tracking issue (#67) for the full decision record.

Current state that shapes the design:

- `plugins/<name>/` trees are installed directly: `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` both point at `./plugins/<name>`.
- Harness adaptation is runtime dispatch: 44 `references/ai-assistant-harnesses/*.md` files, 29 dispatch sentences, frontmatter metadata links, enforced by `tests/test_harness_reference_policy.py`.
- `plugins/mermaid-diagrams/plugin_maintenance/` is an in-plugin generator package with its own `pyproject.toml`, driven by `.github/workflows/sync-mermaid-docs.yml` (PR freshness job + weekly auto-commit job).
- `harness-action-matrix.json` lives in the `adapt-skill-for-ai-harness` skill and maps `actions[action][assistant]`.
- Plugin content contains literal `{{ }}` that must survive any build (mermaid hexagon syntax, Langfuse `{{variable}}` prompts, `{{COMPANY}}` placeholders).
- Root `pyproject.toml` has a `dev` dependency-group (pytest only); tests run with `uv run pytest tests`.

## Goals / Non-Goals

Goals:

- One shared renderer producing both `dist/` trees from `plugins/` deterministically.
- A generator convention any plugin can join without pipeline changes.
- The matrix as the only source of callable names; one wrapper per harness.
- All old-pattern invariants re-expressed as dist-level tests.

Non-Goals:

- No install-time or runtime behavior in published plugins (Jinja is build-only).
- No changes to plugin semantics or skill workflows beyond notation.
- No support for harnesses beyond `ClaudeCode` and `Codex` in this change (the mechanism is generic; only these two are wired).
- No attempt to keep `plugins/` installable directly once manifests repoint.

## Decisions

### D1. Renderer: Python + Jinja2 in the root project

One package, invoked per harness: `uv run python -m plugin_maintenance.render --harness ClaudeCode --output dist/claude-code` (exact module path final at implementation). Jinja2 joins the root `dev` dependency-group. `StrictUndefined` plus explicit post-render checks implement the fail-loud policy.

Alternative — per-plugin render scripts: rejected; the transform is identical for every plugin, and per-plugin code invites drift.

### D2. Root maintenance directory

```
plugin_maintenance/
├── render/            stage-2 renderer (shared)
└── mermaid-diagrams/  stage-1 generator (relocated from the plugin)
```

Stage-1 convention: a subdirectory named after a plugin that exposes the documented generator entrypoint is a generated-plugin declaration; the stage-1 runner iterates subdirectories and runs each entrypoint. `mermaid-diagrams`' package moves here with its history of behavior intact (templates, sync, generated-docs logic); its standalone `pyproject.toml` dissolves into the root project. `sync-mermaid-docs.yml` switches from `uv run --project plugins/mermaid-diagrams` to root-project invocations.

Alternative — keep generators inside plugins: rejected by decision in #67; build code does not ship with plugin content, and one directory keeps all build tooling discoverable.

### D3. Matrix schema: names per action, wrapper per harness

The matrix keeps `actions[action][assistant]` and `lookup_order`. Per-assistant action entries carry a single callable `name` for mapped actions (e.g. `AskUser` → `AskUserQuestion` / `request_user_input`; `TrackTasks` → `TaskCreate` / `update_plan`). A new top-level per-assistant section stores the invocation wrapper exactly once (`Skill({name})` / `${name}`). No `invocations` objects, no per-action forms.

Template context: `harness` (assistant key), `actions` (action → resolved name for the target harness), and one filter that applies the wrapper to any name — matrix-resolved or literal (`{{ actions.AskUser | call }}`, `{{ "dev-workflow:commit" | call }}`). Filter name final at implementation.

Alternative — per-action invocation forms (PR #65): rejected as YAGNI; one wrapper covers every callable by decision in #67.

### D4. Uniform notation is a repo convention, not harness API

`Skill(AskUserQuestion)` / `$request_user_input` are this repo's reference notation for narrative read by LLM agents. Harness docs classify some callables as tools and do not document qualified `$` mentions; this is known and deliberately not encoded (decision record in #67). Tests must not "correct" rendered notation back toward per-surface syntax.

### D5. Publication: committed dist, manifests split per harness

Both `dist/` trees are committed. Each root manifest points at its own tree, which the paired harness resolves from the same git ref — no release branch, no publish job. The repoint and the first committed `dist/` land in the same PR so manifests never reference missing paths.

Alternative — render on a release branch/CI publish: rejected; both marketplaces install from a git ref of this repo, and a second publication surface adds drift risk for zero gain.

### D6. CI

- New PR-gate workflow: run stage 1 + stage 2, then `git diff --exit-code -- plugins/ dist/`, then `uv run pytest tests`.
- `sync-mermaid-docs.yml` auto-commit job: after the docs sync, run stage 2 and widen `file_pattern` to include `dist/`.
- The existing mermaid PR-validation job folds into the new gate (one build, one diff check) or stays as-is if simpler; decided at implementation.

### D7. Tests port, not preserved

`test_harness_reference_policy.py` retires with the pattern. Its vocabulary lists (`FOREIGN_TERMS_BY_REFERENCE`, baseline-tool terms) move into new dist-level and template-source checks. New test modules cover: renderer unit behavior on a fixture plugin, dist purity scans, collision detection, metadata stripping, matrix schema, reproducibility, and manifest-path resolution. `test_ai_assistant_harness_adaptation_skill.py` is rewritten against the new skill content.

## Risks / Trade-offs

- [Committed `dist/` invites hand edits and merge conflicts] → CI freshness gate rejects any divergence; docs state "never edit `dist/`"; conflicts resolve by re-rendering.
- [Repo content roughly triples] → accepted in #67; plugin trees are small text.
- [Uniform notation names things the harness docs call tools] → deliberate (D4); recorded in #67 so future maintainers do not revert it; agents resolve intent from context.
- [Batch migration of 29 skills is wide and mechanical] → pilot one skill end-to-end first; batch follows the proven shape; purity tests catch stragglers.
- [Relocating the mermaid package can break its weekly workflow] → the PR-gate build runs the same entrypoints CI cron uses; workflow changes land in the same PR as the relocation.
- [`plugins/` stops being installable directly] → intended; `.j2` sources make partial installs visibly broken instead of silently wrong.

## Migration Plan

1. Land the pipeline (renderer, relocated mermaid generator, matrix schema change, tests, CI) with a pilot: one small skill authored as `.j2`.
2. Same PR: full render of all plugins, committed `dist/`, both manifests repointed. Manifests and `dist/` change atomically.
3. Follow-up PR(s): batch-migrate the remaining skills (fold reference files inline, delete dispatch sentences and metadata links), rewrite `adapt-skill-for-ai-harness`, update README/AGENTS, bump versions.
4. Rollback: revert the manifest-repoint commit; `plugins/` sources are untouched by rendering, so reverting restores the previous installable state.

## Open Questions

- Filter and module naming (`call` vs `skill_call`; exact package paths) — cosmetic, final at implementation.
- Whether the mermaid PR-validation job merges into the new gate or remains separate (D6) — either satisfies the specs.
