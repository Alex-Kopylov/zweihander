# Claude Code Harness Notes

Use this file only when the active assistant harness is Claude Code.

- Use `Bash` for shell commands such as PR auto-detection and Azure CLI fallback commands.
- Use `Read` when file or line context must be inspected before placing an inline comment.
- Use `AskUserQuestion` when the shared workflow asks the user to choose among multiple PRs or provide a missing PR link.
- Prefer available Azure DevOps MCP tools before the Azure CLI fallback in `references/azure.md`.
