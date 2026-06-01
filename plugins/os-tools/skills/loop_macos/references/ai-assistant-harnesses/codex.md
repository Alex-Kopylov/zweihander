# Codex Harness Notes

Load this file only when the active assistant harness is Codex.

- Treat `/loop` and `/loop_macos` references as user text that can trigger this skill. Do not translate them to unrelated Codex slash commands.
- In Step 5, write new plist files with `apply_patch` when making manual file edits. Use shell commands for launchctl operations and other runtime checks.
- When the skill says to ask the user, use chat or `request_user_input` when a bounded structured choice is useful and available.
