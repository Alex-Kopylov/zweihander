# Generic Plugin Manifest Versions

Use only when discovery reports `plugin`.

## Files

- `plugin.json`

## Edit Rules

- Update only the manifest `"version": "X.Y.Z"` field.
- Do not infer AI Agent manifest requirements from this generic file.
- Validate changed JSON with `jq empty`.
