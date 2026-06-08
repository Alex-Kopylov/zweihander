---
name: version-bumper
description: Bump version strings in project, package, plugin, and marketplace files. Activate when user asks to bump version, release, or says /version-bumper.
argument-hint: "[version] — e.g. 1.2.3, patch, minor, major. If omitted, auto-detected from recent commits."
---

# Version Bumper

## Runtime Loading

At invocation start, load only this file and `scripts/find_versions.py`.
Do not read `references/` until discovery output names the needed files.

Discovery returns a `reference` field for each match. Deduplicate the paths,
read only those files, and use them as file-type-specific edit
rules.

| Pattern | Load when discovered |
|---|---|
| `project`, `metadata` | `references/python-project-files.md` |
| `dunder` | `references/python-module-versions.md` |
| `fastapi` | `references/fastapi-apps.md` |
| `package` | `references/node-packages.md` |
| `plugin` | `references/generic-plugin-manifests.md` |
| `codex-plugin-manifest` | `references/codex-plugin-manifests.md` |
| `claude-code-plugin-manifest` | `references/claude-code-plugin-manifests.md` |
| `marketplace` | `references/marketplace-manifests.md` |
| `codex-marketplace-manifest` | `references/codex-marketplace-manifests.md` |
| `claude-code-marketplace-manifest` | `references/claude-code-marketplace-manifests.md` |

## Version Resolution

If `$ARGUMENTS` is `1.2.3`, use it directly; if `patch`, `minor`, or `major`, increment the current version accordingly.

If no argument is provided, run `git log --oneline -20`: `feat!:` or `BREAKING CHANGE` means **major**, `feat:` means **minor**, otherwise use **patch**.

## Instructions

1. **Discover current version** — run `python scripts/find_versions.py .`.
2. **Load targeted rules** — read only the unique `reference` files reported by discovery.
3. **Resolve target version** using the rules above.
4. **Confirm with user** — show current version, target version, files to update, and loaded references. Wait for approval.
5. **Parallelize broad bumps** — if multiple independent version-bearing files must be bumped, dispatch parallel background agents using a minor LLM. Give each agent only its assigned files and relevant reference files; do not pass Codex context to Claude Code files or Claude Code context to Codex files.
6. **Apply changes** — edit each discovered file according to its loaded reference.
7. **Verify** — re-run the discovery script to confirm the selected files show the new version.
8. **Commit when requested** — stage only changed version files and invoke the `$dev-workflow:commit` skill with type `bump` and description `vOLD → vNEW`.

## Additional Resources

- [scripts/find_versions.py](scripts/find_versions.py)
- [references/](references/)
- [examples/](examples/)
