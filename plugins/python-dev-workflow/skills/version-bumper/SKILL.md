---
name: version-bumper
description: Bump version in project config files (pyproject.toml, FastAPI app, __init__.py, etc.). Activate when user asks to bump version, release, or says /version-bumper.
argument-hint: "[version] — e.g. 1.2.3, patch, minor, major. If omitted, auto-detected from recent commits."
---

# Version Bumper

Bump version strings across project config files in a single pass.

## Supported Files

| File | Pattern |
|------|---------|
| `pyproject.toml` | `version = "X.Y.Z"` under `[project]` or `[tool.poetry]` |
| FastAPI/app `version` | `version="X.Y.Z"` kwarg in `FastAPI(...)` or app constructor |
| `__init__.py` | `__version__ = "X.Y.Z"` |
| `plugin.json` | `"version": "X.Y.Z"` (Claude Code plugins, etc.) |
| `package.json` | `"version": "X.Y.Z"` |
| `setup.cfg` | `version = X.Y.Z` under `[metadata]` |
| `marketplace.json` | `"version": "X.Y.Z"` (Claude Code marketplace) |

## Version Resolution

If `$ARGUMENTS` provides a version (e.g. `1.2.3`, `patch`, `minor`, `major`):
- **Exact** (`1.2.3`): use it directly.
- **Keyword** (`patch`/`minor`/`major`): increment the current version accordingly.

If no argument is provided:
1. Run `git log --oneline -20` to read recent commits.
2. If any commit starts with `feat!:` or contains `BREAKING CHANGE` → **major**.
3. If any commit starts with `feat:` → **minor**.
4. Otherwise → **patch**.

## Instructions

1. **Discover current version** — find version-bearing files using the script:
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/find_versions.py .
   ```
2. **Resolve target version** using the rules above.
3. **Confirm with user** — show current version, target version, and files to update. Wait for approval.
4. **Apply changes** — edit each file, replacing the old version with the new one.
5. **Verify** — re-run the discovery script to confirm all files show the new version.
6. **Commit** — dispatch a subagent (Agent tool) to:
   - Stage all changed version files with `git add`
   - Invoke the `/commit` skill with type `bump` and description `vOLD → vNEW`

## Additional Resources

- For discovery script details, see [scripts/find_versions.py](scripts/find_versions.py)
- For example outputs, see [examples/](examples/)
