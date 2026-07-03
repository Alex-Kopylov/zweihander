# Codex

Use Codex tools for harness-specific actions:

- Ask bounded clarification questions with `request_user_input` when available and appropriate; otherwise use chat.
- Track blueprint work with `update_plan`; keep at most one item `in_progress`.
- Do not assume live multi-agent tools are available. If the active tool list or `tool_search` exposes them, use `spawn_agent` and related controls only as allowed by current harness instructions.
