# Claude Code Harness Notes

Use the shared `SKILL.md` wording directly in Claude Code.

- Ask for confirmation or clarification with `AskUserQuestion`.
- Delegate skill follow-ups with `Skill(dev-workflow:pr-comment)` and `Skill(dev-workflow:commit)`.
- Use `Agent` only when a review comment requires isolated investigation before editing.
