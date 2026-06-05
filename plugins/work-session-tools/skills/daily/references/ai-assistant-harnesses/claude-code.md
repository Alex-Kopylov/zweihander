# Claude Code Harness Notes

Use this file only when the active harness is Claude Code.

## Invocation

Treat `/daily [output-dir]` as the Claude Code slash-command form for this skill.

## Project Context

When source detection or channel discovery needs assistant-specific files, include Claude Code project instructions such as `CLAUDE.md` and Claude Code settings or MCP configuration exposed in the active environment.

Use Claude Code MCP tools that are available in the active session for Slack, Microsoft Teams, Telegram, Azure DevOps, and custom MCP sources. If a configured server is not exposed as an available tool, record that source as unavailable and continue.
