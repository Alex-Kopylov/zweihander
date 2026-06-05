# Claude Code Harness Notes

Use this file only when the active assistant harness is Claude Code.

- Treat the `allowed-tools` names in `SKILL.md` as Claude Code tool names.
- Use `AskUserQuestion` for bounded user choices when structured prompting helps; plain chat is fine for simple prompts.
- Use `WebFetch` when the JD source is a URL.
- Use `Skill` for the optional `resume-tailoring` handoff.
- Preserve `/job-hunt-toolkit:*` slash-command references as plugin command references in user-facing output.
