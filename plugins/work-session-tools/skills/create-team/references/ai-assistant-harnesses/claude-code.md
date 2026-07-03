# Claude Code

Use Claude Code tools for harness-specific actions:

- Ask structured clarification questions with `AskUserQuestion` when useful; plain chat is acceptable for simple clarification.
- Track blueprint work with `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList`, and
  `TaskStop`; avoid deprecated `TaskOutput` when inspecting task output.
- For live multi-agent work, use `TeamCreate`, `SendMessage`, and `TeamDelete` when creating an agent team, or `Agent` for a single delegated subagent.
