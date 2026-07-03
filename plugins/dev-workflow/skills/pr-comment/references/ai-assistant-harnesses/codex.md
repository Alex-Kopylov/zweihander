# Codex Harness Notes

Use this file only when the active assistant harness is Codex.

- When the shared workflow asks the user to choose among multiple PRs or provide a missing PR link, use `request_user_input` if it is available and appropriate for the current mode; otherwise ask in chat.
- Prefer available Azure DevOps MCP tools before the Azure CLI fallback in `references/azure.md`.
