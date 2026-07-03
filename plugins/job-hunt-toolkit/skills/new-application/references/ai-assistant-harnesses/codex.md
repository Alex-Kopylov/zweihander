# Codex Harness Notes

Use this file only when the active assistant harness is Codex.

- Map `AskUserQuestion` to `request_user_input` for bounded choices when available; otherwise ask in chat.
- Load the `resume-tailoring` skill by its available skill entry or `SKILL.md` rather than using a Claude Code `Skill` tool.
- Treat `/job-hunt-toolkit:*` strings as plugin skill or command references. Do not translate them to unrelated Codex slash commands.
