# Claude Code Harness

Use this file only when the active harness is Claude Code.

- User decisions: use `AskUserQuestion` (supports bounded options,
  multiSelect, previews) when a structured choice is useful; otherwise ask in
  chat and wait.
- Delegation: use the `Agent` tool to spawn all selected detector agents in one
  batch, then wait for every spawned agent before reducing findings.
- Skill invocation: use `Skill(dev-workflow:pr-comment)`.
