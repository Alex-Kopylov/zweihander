# Claude Code Plugin Manifest Versions

Use only when discovery reports `claude-code-plugin-manifest`.

## Files

- `**/.claude-plugin/plugin.json`

## Edit Rules

- Update only the Claude Code manifest `"version": "X.Y.Z"` field.
- If a sibling Codex manifest exists for the same plugin, mention it in the
  confirmation step but do not load Codex rules unless discovery also reports
  `codex-plugin-manifest`.
- Validate changed JSON with `jq empty`.
