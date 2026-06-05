# Codex Harness Notes

Use this file only when the active assistant harness is Codex.

- Map shell-command steps to `exec_command`; use `write_stdin` only to continue an existing command session.
- Use `sed`, `nl`, or similar commands through `exec_command` when file or line context must be inspected before placing an inline comment.
- When the shared workflow asks the user to choose among multiple PRs or provide a missing PR link, use `request_user_input` if it is available and appropriate for the current mode; otherwise ask in chat.
- Prefer available Azure DevOps MCP tools before the Azure CLI fallback in `references/azure.md`.
