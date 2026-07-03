# Codex Harness Notes

Use this file only when the active assistant harness is Codex.

- User decisions: use `request_user_input` for bounded choices when available; otherwise ask in chat.
- Resume tailoring handoff: load the `resume-tailoring` skill from the available skills list or by reading its `SKILL.md`.
- Skill references: keep `/job-hunt-toolkit:*` strings as plugin skill or command references; do not rewrite them into unrelated commands.
