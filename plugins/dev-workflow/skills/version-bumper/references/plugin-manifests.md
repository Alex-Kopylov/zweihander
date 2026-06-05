# Plugin Manifest Versions

Use only when discovery reports `plugin` or `plugin-manifest`.

## Files

- `plugin.json`
- `**/.codex-plugin/plugin.json`
- `**/.claude-plugin/plugin.json`

## Edit Rules

- Update only the manifest `"version": "X.Y.Z"` field.
- Keep Codex and Claude Code manifests for the same plugin on the same version unless the user narrows the scope.
- Validate changed JSON with `jq empty`.
