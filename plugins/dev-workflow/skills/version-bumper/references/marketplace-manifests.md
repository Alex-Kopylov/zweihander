# Generic Marketplace Manifest Versions

Use only when discovery reports `marketplace`.

## Files

- `marketplace.json`

## Edit Rules

- Update only marketplace-level `"version": "X.Y.Z"` fields.
- Do not infer Codex or Claude Code marketplace requirements from this generic
  file.
- Do not add version fields to catalog entries that do not already have them.
- Validate changed JSON with `jq empty`.
