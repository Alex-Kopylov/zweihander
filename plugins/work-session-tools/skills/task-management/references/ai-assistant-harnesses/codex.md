# Codex Task Management Adaptation

Use this file only when the active assistant harness is Codex.

Translate task tracking to `update_plan`. Keep plan items concise, maintain at
most one `in_progress` item, and update statuses as work advances. Because
`update_plan` does not expose `blockedBy`, task metadata, or per-task detail
fetching, represent dependencies with ordering and clear step names instead of
inventing `TaskCreate`, `TaskGet`, `TaskList`, or `TaskUpdate` calls.

For delegated agent work, use a Codex subagent tool such as `spawn_agent` only
when it is available in the active tool list or can be discovered through the
active harness's permitted discovery mechanism. If no such tool is available,
continue in the current session and do not invent `Agent`, `TaskOutput`, or
`TaskStop` calls.

Treat `references/orchestration-patterns.md` as Claude Code-baseline examples.
In Codex, translate `TaskCreate` sequences into ordered `update_plan` items and
translate `Agent` examples into permitted Codex subagent calls only when those
calls are actually available.
