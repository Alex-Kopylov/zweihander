# Claude Code Harness Notes

Use these notes only when the active assistant harness is Claude Code.

- Treat `/version-bumper` as slash-command activation for this skill.
- Read the optional target version from `$ARGUMENTS`; an empty `$ARGUMENTS` means auto-detect from recent commits.
- Use Claude Code edit tools such as `Edit` or `MultiEdit` for manual version replacements.
- For the commit step, dispatch the `Agent` tool as the subagent mechanism. In that subagent, stage changed version files with `git add` and invoke the `/commit` skill with type `bump` and description `vOLD -> vNEW`.
- For user approval, ask in chat or use the available user-question tool if the session provides one.
