# Marketplace Manifest Versions

Use only when discovery reports `marketplace` or `marketplace-manifest`.

## Files

- `marketplace.json`
- `**/.claude-plugin/marketplace.json`

## Edit Rules

- Update only marketplace-level `"version": "X.Y.Z"` fields.
- Do not add version fields to catalog entries that do not already have them.
- Validate changed JSON with `jq empty`.
