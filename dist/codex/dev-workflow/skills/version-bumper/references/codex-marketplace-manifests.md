# Codex Marketplace Manifest Versions

Use only when discovery reports `codex-marketplace-manifest`.

## Files

- `**/.agents/plugins/marketplace.json`

## Edit Rules

- Update only Codex marketplace-level `"version": "X.Y.Z"` fields.
- Do not add version fields to catalog entries that do not already have them.
- Validate changed JSON with `jq empty`.
