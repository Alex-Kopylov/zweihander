# Claude Code Harness Notes

Load this file only when the active assistant harness is Claude Code.

- Treat `/loop` and `/loop_macos` references as Claude Code slash-command style user input for this skill.
- In Step 5, write new plist files with the Claude Code `Write` tool. Use `Edit` or `MultiEdit` only when modifying existing files.
- When the skill says to ask the user, use plain chat or `AskUserQuestion` when a structured prompt is useful.
