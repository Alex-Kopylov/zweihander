# Codex Adaptation

- Treat `/ticket-comment-status` in the shared description as a skill activation phrase, not a Codex built-in slash command.
- For the required user confirmation, use chat by default; use `request_user_input` only when it is available and appropriate for a bounded confirmation.
- For posting, use available Codex tools, connectors, or the platform CLI; do not assume a Claude Code MCP tool name exists.
