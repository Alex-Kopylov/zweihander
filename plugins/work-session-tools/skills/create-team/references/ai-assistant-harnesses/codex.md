# Codex

Use this file only when the active harness is Codex.

- User decisions: use `request_user_input` when available; otherwise ask in chat.
- Task tracking: use `update_plan`.
- Delegation: use a subagent tool such as `spawn_agent` when available; otherwise work in the current context.
