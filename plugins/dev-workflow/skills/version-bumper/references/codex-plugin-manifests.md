# Codex Plugin Manifest Versions

Use only when discovery reports `codex-plugin-manifest`.

## Files

- `**/.codex-plugin/plugin.json`

## Edit Rules

- Update only the Codex manifest `"version": "X.Y.Z"` field.
- Keep confirmation scoped to discovered files and loaded references; do not load sibling-runtime rules unless discovery reports them separately.
- Validate changed JSON with `jq empty`.
