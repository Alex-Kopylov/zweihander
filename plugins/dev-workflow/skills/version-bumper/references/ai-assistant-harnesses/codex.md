# Codex Harness Notes

Use this file only when the active harness is Codex.

- Version argument: use the version from the user's request; if absent, auto-detect from recent commits.
- User decisions: use `request_user_input` when available; otherwise ask in chat.
- Delegation: use a subagent tool such as `spawn_agent` when available; otherwise work in the current context.
- Skill invocation: use `$dev-workflow:commit` or load the skill's `SKILL.md`.
