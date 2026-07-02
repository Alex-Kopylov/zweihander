# Claude Code Harness Notes

Use these notes only when the active assistant harness is Claude Code.

- Treat `/version-bumper` as slash-command activation for this skill.
- Read the optional target version from `$ARGUMENTS`; an empty `$ARGUMENTS` means auto-detect from recent commits.
- Use Claude Code edit tools such as `Edit` or `MultiEdit` for manual version replacements.
- For parallel broad bumps, dispatch background `Agent` subagents with a minor model such as `haiku`, one per independent file group.
- For the commit step, `$dev-workflow:commit` in the shared workflow names the commit skill; invoke it with the `Skill` tool as `Skill(dev-workflow:commit)`.
- For user approval, ask in chat or use `AskUserQuestion` when a structured choice is useful.
