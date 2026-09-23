# Node Package Versions

Use only when discovery reports `package`.

## Files

- `package.json`: update the top-level `"version": "X.Y.Z"` field.

## Edit Rules

- Preserve JSON formatting where practical.
- Change only the package's own version, not dependency versions.
- If lockfiles exist, update them only when the package manager normally records the root package version there or the user asks for lockfile updates.
