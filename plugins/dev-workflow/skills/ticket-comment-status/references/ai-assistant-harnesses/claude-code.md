# Claude Code Adaptation

Use the shared `SKILL.md` workflow as written.

- Treat `/ticket-comment-status` as the command-style invocation for this skill when available.
- For the required user confirmation, use plain chat or `AskUserQuestion` if structured confirmation is appropriate.
- For posting, prefer the configured issue tracker tooling in the active harness, including Azure DevOps MCP tools when available; otherwise use the relevant platform CLI.
