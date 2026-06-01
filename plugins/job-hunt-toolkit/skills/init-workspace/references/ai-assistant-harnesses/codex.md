# Codex Harness Notes

Use these notes only when the active harness is Codex.

- Treat `allowed-tools` as Claude Code metadata and use the active Codex tools instead.
- Where the workflow says `AskUserQuestion`, use `request_user_input` when available for bounded choices or required fields; otherwise ask in chat.
- For file creation or edits, use `apply_patch` for manual changes. For file reads, prefer `rg`, `sed`, or `nl` through `exec_command`.
- Where the workflow refers to `Bash`, use `exec_command`; use `write_stdin` only to continue an existing command session.
- Preserve `/job-hunt-toolkit:<skill-name>` references from templates unless the user explicitly asks for Codex-specific wording.
