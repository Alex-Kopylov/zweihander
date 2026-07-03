# Claude Code Harness Notes

The shared `SKILL.md` already uses Claude Code baseline names.

- Invoke `scrub-pdf-metadata` through the `Skill` surface.
- Use `AskUserQuestion` for the final judgment-call confirmations when structured confirmation is useful; plain chat is acceptable when enough.
- Keep `/job-hunt-toolkit:export-pdf` as the plugin slash-command wording when telling the user to re-export.
