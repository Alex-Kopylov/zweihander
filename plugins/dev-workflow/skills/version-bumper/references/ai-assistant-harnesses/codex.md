# Codex Harness Notes

Use these notes only when the active assistant harness is Codex.

- Treat a user-supplied version in the request as the argument that Claude Code skills call `$ARGUMENTS`; if absent, auto-detect from recent commits.
- Do not assume `/version-bumper` or `/commit` exist as Codex slash commands. Activate this skill and the commit workflow through the available skills list, using the matching `dev-workflow:commit` skill when available.
- Use Codex editing conventions for manual version replacements, typically `apply_patch`.
- For the commit step, use Codex subagent delegation only if a permitted subagent tool such as `spawn_agent` is available or discoverable. Otherwise, perform the staging and commit-skill workflow in the current context.
- Ask for approval in chat or with `request_user_input` when that tool is available and appropriate.
