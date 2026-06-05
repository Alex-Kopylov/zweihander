# Codex Harness

Translate the shared Claude Code-baseline workflow to Codex surfaces only where
needed.

- Use `request_user_input` for bounded item decisions when available; otherwise
  ask in chat.
- `request_user_input` options support labels and descriptions. Present proposed
  code/config previews in chat before the request, or fold brief previews into
  the option description.
- Use `exec_command` for shell commands and `write_stdin` to continue running
  command sessions.
- Use shell readers such as `sed`, `nl`, and `rg` through `exec_command` for
  scoped file reads.
- Use `apply_patch` for manual edits. Mechanical rewrites may use existing
  formatters.
