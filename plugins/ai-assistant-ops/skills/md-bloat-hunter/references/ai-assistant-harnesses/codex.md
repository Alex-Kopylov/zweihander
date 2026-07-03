# Codex Harness

Use this file only when the active harness is Codex.

- User decisions: use `request_user_input` when available; otherwise ask in
  chat and wait.
- Delegation: use a subagent tool such as `spawn_agent` when available to run
  all selected detector agents in one batch; otherwise run detector prompts in
  the current context.
- Wait for every spawned agent before reducing findings.
- Skill invocation: use `$dev-workflow:pr-comment` or load the skill's
  `SKILL.md`.
