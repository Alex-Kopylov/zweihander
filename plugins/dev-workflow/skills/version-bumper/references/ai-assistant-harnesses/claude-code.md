# Claude Code Harness Notes

Use this file only when the active harness is Claude Code.

- Version argument: `$ARGUMENTS` holds the slash-command argument; if absent, auto-detect from recent commits.
- User decisions: use `AskUserQuestion` when approval needs a structured choice; otherwise ask in chat.
- Delegation: use the `Agent` tool with a minor model such as `haiku`, one per independent file group.
- Skill invocation: use `Skill(dev-workflow:commit)`.
