# Claude Code Harness Adaptation

Use this file only when the active harness is Claude Code.

## Conversation logs

- Default logs live under `~/.claude/projects/<encoded-project>/*.jsonl`, where `<encoded-project>` follows the shared Step 1 path encoding.
- For multi-agent sessions, include relevant `Agent`, `TeamCreate`, or parallel `TaskCreate` subagent logs modified near the main log timestamp.

## Runtime operations

- Parallel insight extraction: use `Agent` to run each hunter prompt from `agents/` concurrently.
- User decisions: use the `AskUserQuestion` examples in the shared workflow.
- Task tracking: use `TaskCreate`, `TaskList`, `TaskUpdate`, `TaskGet`, `TaskOutput`, and `TaskStop` as needed to track selected findings through storage or skip decisions.
