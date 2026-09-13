# Claude Code Task Management Adaptation

Use the shared `SKILL.md` instructions as written for Claude Code.

For task tracking, use `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, and
`TaskStop` when those tools are available. Use `TaskOutput` for background
agent output when this target skill's background-agent workflow needs it.

For agent delegation, use the `Agent` tool. `Explore`, `Plan`,
`general-purpose`, named subagents, and the `haiku`, `sonnet`, and `opus`
model labels are Claude Code vocabulary; use them only when the active
environment exposes them.
