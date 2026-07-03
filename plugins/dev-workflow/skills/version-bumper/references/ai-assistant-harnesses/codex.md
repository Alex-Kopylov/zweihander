# Codex Harness Notes

Use these notes only when the active assistant harness is Codex.

- Treat a user-supplied version in the request as the argument that Claude Code skills call `$ARGUMENTS`; if absent, auto-detect from recent commits.
- Do not assume `/version-bumper` exists as a Codex slash command; treat it as an activation phrase for this skill.
- `$dev-workflow:commit` in the shared workflow is already the Codex direct-invocation form; use the matching skill from the available skills list.
- For parallel broad bumps, use a permitted subagent tool such as `spawn_agent` when available or discoverable; otherwise bump the file groups sequentially in the current context.
- Ask for approval in chat or with `request_user_input` when that tool is available and appropriate.
