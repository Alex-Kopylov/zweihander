# Codex Harness Notes

Use these notes only when the active assistant harness is Codex.

- A user-supplied version in the request fills the `$ARGUMENTS` value; if absent, auto-detect from recent commits.
- Skill activation: when the user names `version-bumper`, run this skill; no separate slash command is required.
- `$dev-workflow:commit` in the shared workflow is already the Codex direct-invocation form; use the matching skill from the available skills list.
- For parallel broad bumps, use a permitted subagent tool such as `spawn_agent` when available or discoverable; otherwise bump the file groups sequentially in the current context.
- Ask for approval in chat or with `request_user_input` when that tool is available and appropriate.
