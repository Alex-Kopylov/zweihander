# Codex Harness Notes

Use this file only when the active harness is Codex.

- User decisions: use `request_user_input` for bounded choices when available, or plain chat for open-ended resume discovery and confirmations.
- Delegation: use a subagent tool such as `spawn_agent` when available; otherwise work in the current context.
- Skill invocation: use `$job-hunt-toolkit:export-pdf` or load the skill's `SKILL.md`.
