# Codex Harness Notes

Use these notes only when the active harness is Codex.

## Discovery

- Include Codex context files when present:

  ```bash
  find . \( -name "AGENTS.md" -o -name ".codex.md" -o -name ".codex.local.md" \) 2>/dev/null | head -50
  ```

- Treat `./.codex.local.md` as local personal settings and
  `~/.codex/AGENTS.md` as user-wide defaults when explaining context locations.
- Account for parent-directory and nested `AGENTS.md` discovery in monorepos.

## User Tips

- Do not mention Claude Code's `#` shortcut. For personal preferences, point
  users to `.codex.local.md` or `~/.codex/AGENTS.md`.
