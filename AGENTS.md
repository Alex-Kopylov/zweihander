# Zweihander

## Notes for Developers

This repository is a personal plugin marketplace for both Codex and Claude Code.
Keep user-facing installation, usage, and plugin catalog content in `README.md`.
Keep development, maintenance, and release workflow guidance in this file.

## Supported Runtimes

| Runtime | Marketplace metadata | Plugin metadata (authored) | Installed source |
|---|---|---|---|
| Codex | `.agents/plugins/marketplace.json` | `plugins/*/.codex-plugin/plugin.json` | `dist/codex/<plugin-name>` |
| Claude Code | `.claude-plugin/marketplace.json` | `plugins/*/.claude-plugin/plugin.json` | `dist/claude-code/<plugin-name>` |

The marketplace install identifier is `zweihander`; the display name is
`Zweihander`.

## Repository Layout

- `.agents/plugins/marketplace.json` defines the Codex marketplace catalog.
- `.claude-plugin/marketplace.json` defines the Claude Code marketplace catalog.
- `plugins/<plugin-name>/` contains one marketplace plugin.
- `plugins/<plugin-name>/skills/` contains skill folders.
- `plugins/<plugin-name>/agents/` contains agent definitions when the plugin has agents.
- `plugins/<plugin-name>/references/` contains reusable reference docs for plugin skills.
- `plugins/<plugin-name>/.codex-plugin/plugin.json` contains Codex plugin metadata.
- `plugins/<plugin-name>/.claude-plugin/plugin.json` contains Claude Code plugin metadata.
- `plugin_maintenance/` contains the build tooling: `generate.py` (stage-1
  runner), `render.py` (stage-2 renderer), `build.py` (full build), and
  `generators/<plugin_name>/` packages for plugins with generated content.
- `dist/claude-code/` and `dist/codex/` are the committed rendered trees the
  marketplace manifests install from.

## Build Pipeline

Plugins are authored once under `plugins/` and rendered per harness into
`dist/`. **Author in `plugins/`; never edit `dist/`** — CI rejects any commit
where `dist/` differs from a fresh build.

The build has two stages:

1. **Generation**: every package under `plugin_maintenance/generators/` runs
   its zero-argument `generate()` in-place under `plugins/<plugin-name>/`.
   Generators are offline, idempotent, and deterministic; anything fetching
   external content lives outside the build (for example the weekly mermaid
   sync workflow).
2. **Distribution**: the renderer emits one complete installable tree per
   harness containing exactly the plugins that harness's marketplace manifest
   lists. Plain files copy byte-for-byte (mode bits preserved); `X.j2`
   templates render with the harness context and emit `X`; `X` plus `X.j2`
   fails the build. Files named `AGENTS.md`, `CLAUDE.md`, or `README.md` and
   the other runtime's plugin metadata directory are never emitted.

Build commands:

```shell
uv run python -m plugin_maintenance.build
```

runs the full build (both stages, both trees). To run one piece:

```shell
uv run python -m plugin_maintenance.generate
uv run python -m plugin_maintenance.render --harness ClaudeCode --output dist/claude-code
uv run python -m plugin_maintenance.render --harness Codex --output dist/codex
```

Harness-specific wording in skills lives in `.j2` templates that resolve
callable names from the action matrix at
`plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness/references/harness-action-matrix.json`.
Use the `adapt-skill-for-ai-harness` skill when converting a skill's
harness-specific wording into template form.

## Development Workflow

1. Update plugin files under `plugins/<plugin-name>/`.
2. Update both runtime manifests when plugin metadata changes.
3. Update both marketplace files when adding, removing, renaming, or recategorizing plugins.
4. Update `README.md` when user-facing install, usage, or catalog information changes.
5. Keep `third_party/` links, notices, and license copies current when
   third-party material changes.
6. Run the full build and commit the resulting `dist/` changes together with
   the source changes:

```shell
uv run python -m plugin_maintenance.build
```

7. Run the tests and JSON validation before finishing:

```shell
uv run pytest tests
jq empty .agents/plugins/marketplace.json .claude-plugin/marketplace.json
find plugins dist -path '*/plugin.json' -print0 | xargs -0 jq empty
```

8. Run Markdown whitespace checks before finishing:

```shell
git diff --check
```

## Versioning

When changing plugin or marketplace content, bump the relevant versions according
to the official Claude Code and Codex plugin marketplace documentation.

Use this repo's `version-bumper` skill at
`plugins/dev-workflow/skills/version-bumper/SKILL.md` to update
version-bearing files such as `plugin.json`, `marketplace.json`, and package
metadata.

README-only or AGENTS-only edits do not require a plugin version bump unless
they also change plugin behavior, manifests, or marketplace metadata.

## Shared Runtime Instructions

Use `AGENTS.md` as the shared instruction file when a plugin needs runtime
context. Runtimes that read `AGENTS.md` can consume it directly.

For runtimes that read `CLAUDE.md`, keep a sibling `CLAUDE.md` next to every
`AGENTS.md` and import the shared file:

```md
@AGENTS.md
```

This keeps Codex and Claude Code on the same instructions without copying
content between files.

## Plugin Catalog Maintenance

When adding a plugin:

- Add `plugins/<plugin-name>/.codex-plugin/plugin.json`.
- Add `plugins/<plugin-name>/.claude-plugin/plugin.json`.
- Add the plugin to `.agents/plugins/marketplace.json`.
- Add the plugin to `.claude-plugin/marketplace.json`.
- Each manifest is the inclusion list for its own `dist/` tree; a plugin
  listed in only one manifest ships to only that harness.
- Run the full build so both `dist/` trees include the plugin.
- Add a user-facing section to `README.md`.
- If the plugin has more than one skill, put the README plugin details inside a
  Markdown `<details>` spoiler.

When removing or renaming a plugin, update all of the same locations and check
for stale references with `rg '<plugin-name>'`.

## Official References

- Codex plugin marketplace CLI:
  `https://developers.openai.com/codex/cli/reference#codex-plugin-marketplace`
- Claude Code plugin marketplaces:
  `https://code.claude.com/docs/en/plugin-marketplaces`
