# Codex Harness Notes

Use this file only when the active assistant harness is Codex.

- Map file reads to scoped shell reads such as `rg`, `sed`, or `nl` through `exec_command`.
- Map file creation and edits to `apply_patch` for manual changes; use `exec_command` for shell actions such as `mkdir`, globbing, copying, and environment checks.
- Map `AskUserQuestion` to `request_user_input` for bounded choices when available; otherwise ask in chat.
- Map `WebFetch` to `web.run` when the JD source is a URL.
- Load the `resume-tailoring` skill by its available skill entry or `SKILL.md` rather than using a Claude Code `Skill` tool.
- Treat `/job-hunt-toolkit:*` strings as plugin skill or command references. Do not translate them to unrelated Codex slash commands.
