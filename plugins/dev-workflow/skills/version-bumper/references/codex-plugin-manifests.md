# Codex Plugin Manifest Versions

Use only when discovery reports `codex-plugin-manifest`.

## Files

- `**/.codex-plugin/plugin.json`

## Edit Rules

- Update only the Codex manifest `"version": "X.Y.Z"` field.
- If a sibling Claude Code manifest exists for the same plugin, mention it in the
  confirmation step but do not load Claude Code rules unless discovery also
  reports `claude-code-plugin-manifest`.
- Validate changed JSON with `jq empty`.
