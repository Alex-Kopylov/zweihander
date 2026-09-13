# Claude Code Harness Adaptation

Use this file only when the active harness is Claude Code.

## Conversation logs

- Default logs live under `~/.claude/projects/<encoded-project>/*.jsonl`, where `<encoded-project>` follows the shared Step 1 path encoding.
- For multi-agent sessions, include relevant `Agent`, `TeamCreate`, or parallel `TaskCreate` subagent logs modified near the main log timestamp.

## Runtime operations

- Delegation: use the `Agent` tool to run each hunter prompt from `agents/`
  concurrently.
- User decisions: use `AskUserQuestion` (supports bounded options,
  multiSelect, previews).
- Task tracking: use `TaskCreate`/`TaskUpdate`; keep one selected finding
  `in_progress` at a time and use `TaskList` to re-orient when needed.
- Skill invocation: use `Skill(ai-assistant-ops:agents-md-improver)`.
