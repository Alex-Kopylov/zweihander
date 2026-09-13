# Codex Task Management Adaptation

Use this file only when the active assistant harness is Codex.

Track work as ordered `update_plan` items. Keep plan items concise, maintain at
most one `in_progress` item, and update statuses as work advances. Codex has no
background task graph; represent dependencies with ordering and clear step names
instead of inventing unavailable task-management calls.

For delegated work, use a Codex subagent tool such as `spawn_agent` only when it
is available in the active tool list or can be discovered through the active
harness's permitted discovery mechanism. If no such tool is available, continue
in the current session and do not invent unavailable task or delegation calls.

Use `references/orchestration-patterns.md` as pattern examples: emulate its task
sequences with ordered `update_plan` items and its delegation examples with
permitted Codex subagent calls only when those calls are actually available.
