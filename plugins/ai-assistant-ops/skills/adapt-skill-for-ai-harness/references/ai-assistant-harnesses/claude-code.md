# Claude Code Harness Reference

Checked: 2026-05-30

Sources:

- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/tools-reference
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/plugins-reference

Use this file only when adapting a target skill for Claude Code-specific wording.

## Skill Invocation

Claude Code invokes plugin skills with the plugin namespace, such as `/plugin-name:skill-name`. Shared skill text may keep Claude Code command vocabulary as the baseline.

Skills can include supporting files next to `SKILL.md`; reference files should be loaded only when needed. Plugin skills live under `<plugin>/skills/<skill-name>/SKILL.md`.

## Tool Names

Use these Claude Code tool names when a target skill needs Claude-specific wording: `Read`, `Write`, `Edit`, `MultiEdit`, `Glob`, `Grep`, `Bash`, `Agent`, `Skill`, `AskUserQuestion`, `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, `TaskStop`, `TeamCreate`, `TeamDelete`, `SendMessage`, `WebFetch`, `WebSearch`.

Prefer `Agent` for new subagent guidance. The legacy `Task(...)` name remains an alias in older material, but new guidance should use `Agent`. Treat `TaskOutput` as deprecated wording; prefer reading the task output file path when that applies.

## File Operations

Use `Read` before targeted edits. `Edit` performs exact string replacement and is sensitive to whitespace. Use `Write` only when creating or replacing a full file is intended. Use `Glob` and `Grep` for file discovery and content search.

Use `Bash` for shell commands, and remember that command environment changes do not persist across separate tool calls unless Claude Code-specific configuration arranges that behavior.

## Questions And Tasks

Use `AskUserQuestion` when the workflow needs structured clarification. Use `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, `TaskStop`, and related team tools only in Claude Code-specific guidance, not in shared skill text that should also work in Codex.

## Plugin Notes

Claude Code plugin manifests live at `.claude-plugin/plugin.json`. Plugin components may include `skills/`, `agents/`, hooks, MCP servers, and other Claude Code-specific components.
