# Claude Code Harness Notes

Use Claude Code's native tools for Obsidian vault work:

- Read notes with `Read`.
- List notes with `Glob`.
- Search note contents with `Grep`.
- Edit notes with `Edit`, `MultiEdit`, or `Write`.
- Use `Bash` only when resolving environment variables, checking fallback paths,
  or doing a simple append that is clearer than an edit.

Resolve `OBSIDIAN_VAULT_PATH` to an absolute path before using file tools.
