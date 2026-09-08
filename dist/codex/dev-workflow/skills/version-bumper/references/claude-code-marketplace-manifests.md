# Claude Code Marketplace Manifest Versions

Use only when discovery reports `claude-code-marketplace-manifest`.

## Files

- `**/.claude-plugin/marketplace.json`

## Edit Rules

- Update only Claude Code marketplace-level `"version": "X.Y.Z"` fields.
- Do not add version fields to catalog entries that do not already have them.
- Validate changed JSON with `jq empty`.
