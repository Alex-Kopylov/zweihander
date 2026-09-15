# Zweihander

## Notes for Developers

This repository is a personal plugin marketplace for both Codex and Claude Code.
Keep user-facing installation, usage, and plugin catalog content in `README.md`.
Keep development, maintenance, and release workflow guidance in this file.

## Supported Runtimes

| Runtime | Marketplace metadata | Plugin metadata |
|---|---|---|
| Codex | `.agents/plugins/marketplace.json` | `plugins/*/.codex-plugin/plugin.json` |
| Claude Code | `.claude-plugin/marketplace.json` | `plugins/*/.claude-plugin/plugin.json` |

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

## Skill Design

- **Tiny skills, fat references.** Keep routing `SKILL.md` files small; put depth in references and examples.
- **Skill content progressive disclosure.** Load only the reference branch the current task needs.

### Gateway Skills vs Fine-Grained Skills

Both forms follow the same design principles; the developer decides whether
their workflows stay in `SKILL.md` or are split into references.

Fine-grained skills may exist to preserve explicit user control over
distinct processes, not because their content cannot be combined. When
fine-grained control is needed, do not bury those operations under the
`references/` or `examples/` folders of a gateway skill. Before
consolidating them, kindly push back and ask whether the user actually wants to
trade those explicit control points for a single gateway.

## Development Workflow

1. Update plugin files under `plugins/<plugin-name>/`.
2. Update both runtime manifests when plugin metadata changes.
3. Update both marketplace files when adding, removing, renaming, or recategorizing plugins.
4. Update `README.md` when user-facing install, usage, or catalog information changes.
5. Keep `third_party/` links, notices, and license copies current when
   third-party material changes.
6. Run JSON validation before finishing:

```shell
jq empty .agents/plugins/marketplace.json .claude-plugin/marketplace.json
find plugins -path '*/plugin.json' -print0 | xargs -0 jq empty
```

7. Run Markdown whitespace checks before finishing:

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
