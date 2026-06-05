---
name: version-bumper
description: Bump version strings in project, package, plugin, and marketplace files. Activate when user asks to bump version, release, or says /version-bumper.
argument-hint: "[version] — e.g. 1.2.3, patch, minor, major. If omitted, auto-detected from recent commits."
---

# Version Bumper

## Runtime Loading

At invocation start, load only this file and `scripts/find_versions.py`.
Do not read `references/` until discovery output names the needed files.

Discovery returns a `reference` field for each match. Deduplicate those paths,
read only the referenced files, and use them as the file-type-specific edit
rules.

| Pattern | Load when discovered |
|---|---|
| `project`, `metadata` | `references/python-project-files.md` |
| `dunder` | `references/python-module-versions.md` |
| `fastapi` | `references/fastapi-apps.md` |
| `package` | `references/node-packages.md` |
| `plugin`, `plugin-manifest` | `references/plugin-manifests.md` |
| `marketplace`, `marketplace-manifest` | `references/marketplace-manifests.md` |

## Version Resolution

If `$ARGUMENTS` is `1.2.3`, use it directly; if it is `patch`, `minor`, or `major`, increment the current version accordingly.

If no argument is provided, run `git log --oneline -20`: `feat!:` or `BREAKING CHANGE` means **major**, `feat:` means **minor**, otherwise use **patch**.

## Instructions

1. **Discover current version** — run `python scripts/find_versions.py .`.
2. **Load targeted rules** — read only the unique `reference` files reported by discovery.
3. **Resolve target version** using the rules above.
4. **Confirm with user** — show current version, target version, files to update, and loaded references. Wait for approval.
5. **Apply changes** — edit each discovered file according to its loaded reference.
6. **Verify** — re-run the discovery script to confirm the selected files show the new version.
7. **Commit when requested** — stage only changed version files and invoke the `/commit` skill with type `bump` and description `vOLD → vNEW`.

## Additional Resources

- [scripts/find_versions.py](scripts/find_versions.py)
- [references/](references/)
- [examples/](examples/)
