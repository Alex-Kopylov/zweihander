# Claude Code Harness Notes

Use these notes only when the active harness is Claude Code.

## Discovery

- Keep `AGENTS.md` as the shared project-context file when the repository uses
  that convention.
- If the repository keeps Claude Code adapters next to shared AGENTS.md files,
  check sibling `CLAUDE.md` files for `@AGENTS.md` imports and treat them as
  harness adapters unless the user asks to audit them directly.

## Applying Updates

- After user approval, apply changes with Claude Code's `Edit`, `MultiEdit`, or
  `Write` tools.

## User Tips

- Mention the `#` shortcut only when it is relevant to capturing Claude Code
  memory in the active session.
