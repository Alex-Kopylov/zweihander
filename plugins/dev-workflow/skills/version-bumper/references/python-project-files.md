# Python Project Version Files

Use only when discovery reports `project` or `metadata`.

## Files

- `pyproject.toml`: update the `version = "X.Y.Z"` value under `[project]` or `[tool.poetry]`.
- `setup.cfg`: update the `version = X.Y.Z` value under `[metadata]`.

## Edit Rules

- Preserve quote style, spacing, section order, and comments.
- Change only the package version field, not dependency constraints or tool versions.
- If both `pyproject.toml` and `setup.cfg` exist with the same current version, keep them in sync unless the user narrows the scope.
