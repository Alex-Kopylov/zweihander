# Codex Harness Notes

Use Codex's native tools for Obsidian vault work:

- Read notes with scoped shell commands such as `sed` or `nl` through
  `exec_command`.
- List notes with `rg --files` through `exec_command`.
- Search note contents with `rg` through `exec_command`.
- Edit notes with `apply_patch` when the vault is inside the workspace. If the
  vault is outside the workspace, use the safest available local file-edit
  workflow.
- Use `exec_command` when resolving environment variables, checking fallback
  paths, or doing a simple append that is clearer than a patch.

Resolve `OBSIDIAN_VAULT_PATH` to an absolute path before using file tools.
