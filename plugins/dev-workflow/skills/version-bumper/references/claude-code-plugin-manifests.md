# Claude Code Plugin Manifest Versions

Use only when discovery reports `claude-code-plugin-manifest`.

## Files

- `**/.claude-plugin/plugin.json`

## Edit Rules

- Update only the Claude Code manifest `"version": "X.Y.Z"` field.
- Keep confirmation scoped to discovered files and loaded references; do not load sibling-runtime rules unless discovery reports them separately.
- Validate changed JSON with `jq empty`.
