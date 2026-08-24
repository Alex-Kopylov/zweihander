# Design: harness-dist-pipeline

## Context

See `proposal.md` for motivation and the tracking issue (#67) for the full decision record.

Current state that shapes the design:

- `plugins/<name>/` trees are installed directly: `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` both point at `./plugins/<name>`.
- The two catalogs already diverge: the Claude Code manifest lists 12 plugins, the Codex manifest 13. `run-and-verify-app` — a Codex port of Claude Code's built-in `run` skill — has no `.claude-plugin/` metadata and no Claude Code manifest entry.
- Harness adaptation is runtime dispatch: 55 `references/ai-assistant-harnesses/*.md` files (50 top-level plus 5 under langfuse's nested sub-skills; `create-dataset` carries only `claude-code.md`), 29 dispatch sentences, frontmatter metadata links, enforced by `tests/test_harness_reference_policy.py`. Counts measured at `8d3edd5`: `find plugins -path '*/references/ai-assistant-harnesses/*' -type f | wc -l` → 55; `rg -l 'Depending on who you are as an AI agent' plugins | wc -l` → 29.
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
├── render/                stage-2 renderer (shared)
└── generators/
    └── mermaid_diagrams/  stage-1 generator (relocated from the plugin)
```

Generator convention: a package under `generators/`, named for its plugin (underscores; the hyphenated plugin name lives in a constant inside the package), exposing a zero-argument `generate()` entrypoint that is offline, idempotent, and deterministic. The stage-1 runner iterates `generators/*` only — `render/` can never be mistaken for a generator. Anything that fetches external content (the mermaid upstream sync) lives outside the build as a separate updater invoked by the weekly workflow. `mermaid-diagrams`' package moves here (templates and generated-docs logic intact); its standalone `pyproject.toml` and `uv.lock` dissolve into the root project; `sync-mermaid-docs.yml` switches to root-project invocations.

Alternative — keep generators inside plugins: rejected by decision in #67; build code does not ship with plugin content, and one directory keeps all build tooling discoverable.

### D3. Matrix schema: names per action, wrapper per harness

The matrix keeps the flat `actions[action][assistant]` shape and `lookup_order`; action keys stay TitleCase. Every action carries a `callable` flag:

- Callable actions map to exactly one `name` per assistant (`AskUser` → `AskUserQuestion` / `request_user_input`). Several actions may resolve to the same name: task tracking splits into per-operation actions — `CreateTask`, `GetTask`, `ListTasks`, `UpdateTask`, `StopTask` — mapping to the five Claude Code task tools and all mapping to `update_plan` on Codex. Action keys never equal a callable name (`CreateTask` vs `TaskCreate`), so the "no literal names in templates" check stays a plain text scan.
- Non-callable actions (`PluginManifest`, `SlashCommand`) carry reference material (paths, command lists) and are exempt from the name-and-wrapper rule.
- `InvokeSkill` dissolves — invoking a skill is the wrapper itself. `surface`, `terms`, and the other multi-term lists are dropped.

A top-level per-assistant section stores the invocation wrapper exactly once (`Skill({name})` / `${name}`). PR #65's per-action `invocations` design is not adopted (never merged, nothing to remove).

Template context: `harness` (assistant key), `actions` (action → resolved name for the target harness), and one filter that applies the wrapper to any name — matrix-resolved or literal (`{{ actions.AskUser | call }}`, `{{ "dev-workflow:commit" | call }}`). Filter name final at implementation.

Alternative — per-action invocation forms (PR #65): rejected as YAGNI; one wrapper covers every callable by decision in #67. Alternative — one umbrella `TrackTasks` action with a single name: rejected; it leaves four of the five Claude Code task tools unreferenceable from templates.

### D4. Uniform notation is a repo convention, not harness API

`Skill(AskUserQuestion)` / `$request_user_input` are this repo's reference notation for narrative read by LLM agents. Harness docs classify some callables as tools and do not document qualified `$` mentions; this is known and deliberately not encoded (decision record in #67). Tests must not "correct" rendered notation back toward per-surface syntax. The
anti-revert half of this decision is normative in
`specs/harness-invocation-notation` — "Notation is a repo convention, not vendor
API" — so it survives into the main specs when this change is archived and this
design document moves to `openspec/changes/archive/`.

### D5. Publication: committed dist, manifests split per harness

Both `dist/` trees are committed. Each root manifest points at its own tree, which the paired harness resolves from the same git ref — no release branch, no publish job. The repoint and the first committed `dist/` land in the same PR so manifests never reference missing paths.

Alternative — render on a release branch/CI publish: rejected; both marketplaces install from a git ref of this repo, and a second publication surface adds drift risk for zero gain.

### D6. CI

- PR-gate workflow: full build (stage 1 + stage 2), then `git diff --exit-code` over the whole tree (catches stale `dist/` and stale generated files wherever they live), then `uv run pytest tests`.
- Weekly mermaid job: fetch the upstream snapshot, delete the temporary checkout, run the same full build, then open a pull request with the combined `plugins/` + `dist/` changes — no direct pushes. The PR passes the standard gate like any other change.
- The old mermaid PR-validation job dissolves into the gate: one build, one diff check.

### D7. Tests port, not preserved

`test_harness_reference_policy.py` retires with the pattern. The foreign-vocabulary scan is rebuilt, not ported: the foreign-name lists are derived from the matrix itself (every callable name of the other harness), the scan runs only on files rendered from `.j2` sources, and a spec-level exemption list — successor of the retired `AGNOSTIC_EXEMPT` — covers files whose subject matter is another harness (seeded with the version-bumper harness reference docs and the action matrix file). `Skill(` and `$<name>` are required wrappers now, not foreign terms. New test modules cover: renderer unit behavior on a fixture plugin, dist purity scans, collision detection, metadata stripping, matrix schema, reproducibility, and manifest-path resolution. `test_ai_assistant_harness_adaptation_skill.py` is rewritten against the new skill content. All test work in this change is authored with the repo's own `python-dev-workflow:tests-manager` skill.

### D8. Catalog membership is per harness, defined by the harness's manifest

Each root marketplace manifest is the explicit inclusion list for its own `dist/` tree: the renderer emits exactly the plugins that manifest lists, nothing else. The catalogs may diverge — `run-and-verify-app` duplicates Claude Code's built-in `run` skill, so it exists only for Codex and only in the Codex catalog. Divergence is normal and supported.

Alternative — force both trees to carry every plugin under `plugins/`: rejected; it manufactures an uninstallable `dist/claude-code/run-and-verify-app/` (no `.claude-plugin/` metadata exists to ship). A hand-kept inclusion list in build config: rejected as a second source of truth next to the manifests.

### D9. Development files never reach dist

Files named `AGENTS.md`, `CLAUDE.md`, or `README.md` anywhere under `plugins/` are authoring-time files; the renderer skips them in both trees. Neither manifest references them (the only path field in any `plugin.json` is `"skills": "./skills/"`). This also dissolves the symlink question: the only symlinks under `plugins/` are the two `CLAUDE.md → AGENTS.md` links. Copied and rendered files preserve the source file's mode bits, so shipped shell scripts stay executable.

The rule is a predicate on the *emitted* name, not on the source name, so `AGENTS.md.j2` is caught too. It fails the build rather than being skipped: a template is deliberate authoring, and silently dropping one looks like data loss, so the renderer says what it would have emitted and why it cannot. This is the same fail-loud stance as the plain/template collision.

The rule has a corollary the authoring side must respect: a plugin's runtime context cannot live in a plugin-level `AGENTS.md`, because that file ships to nobody and any skill linking to it gets a dangling path once the manifests install from `dist/`. Runtime context belongs in `plugins/<name>/references/<topic>.md` or in the `SKILL.md`. Root `AGENTS.md` is unaffected — it is repository instructions, not plugin content.

### D10. `.gitignore` is the one declaration of what is not content

Tooling drops artifacts inside `plugins/`: `__pycache__/` from a plugin's own scripts and tests, `.DS_Store`, scratch notes. The renderer walks the source directory, so without a filter these are copied verbatim into a published tree — and because `.gitignore` hides them from `git diff`, the freshness gate never notices the local tree diverging from the committed one.

The filter reuses the repository's root `.gitignore` rather than keeping a second exclusion list beside it, which would drift. It reads the file, never the git index: stage 1 writes generated files into `plugins/` before anything commits them, so an index-driven test would drop freshly generated content from the tree.

### D11. The published tree takes the mode of `dist/`

The renderer builds into a staging directory and renames it into place, so the published tree inherits whatever mode staging had. `tempfile.mkdtemp` always creates `0o700` and `rename` keeps it, which would publish a tree no other user can traverse — invisible to the freshness gate, because git does not track directory modes.

Staging takes the mode of `dist/` itself before the rename. Preserving the *existing* `dist/<harness>/` mode was rejected: a tree already left private by an earlier build would stay private forever. Reading the process umask was rejected as a thread-unsafe global mutation. Taking the parent's mode self-heals and keeps the published mode a pure function of the source tree, which is what the freshness requirement asks of every other published attribute.

## Risks / Trade-offs

- [Committed `dist/` invites hand edits and merge conflicts] → CI freshness gate rejects any divergence; docs state "never edit `dist/`"; conflicts resolve by re-rendering.
- [Repo content roughly triples] → accepted in #67; plugin trees are small text.
- [Uniform notation names things the harness docs call tools] → deliberate (D4); recorded in #67 so future maintainers do not revert it; agents resolve intent from context.
- [Batch migration of 28 skills is wide and mechanical] → pilot one skill end-to-end first inside the PR; batch follows the proven shape; purity tests catch stragglers.
- [Relocating the mermaid package can break its weekly workflow] → the weekly job runs the same full build as the PR gate after its fetch step; workflow changes land in the same PR as the relocation.
- [`plugins/` stops being installable directly] → intended; `.j2` sources make partial installs visibly broken instead of silently wrong.

## Migration Plan

Everything lands in a single PR: pipeline, matrix schema change, full migration of all skills, committed `dist/`, manifest repoint, CI, the adaptation-skill rewrite, and docs. Dist-level invariants therefore hold from the first commit that publishes `dist/`, and manifests never reference missing paths.

Development order inside the PR is test-first (TDD), per `tasks.md`: each behavior's failing tests land before its implementation, and the pilot skill is converted and verified end-to-end before the batch.

Rollback: revert the PR. Sources, manifests, and `dist/` return to the pre-change state together.

## Open Questions

- Filter and module naming (`call` vs `skill_call`; exact package paths) — cosmetic, final at implementation.
