# Codex Harness Adaptation

Use this file only when the active harness is Codex.

## Conversation logs

- Prefer an explicit user-provided log path. Otherwise search Codex session logs under `~/.codex/sessions/` for recent `.jsonl` files that match the current project path or session timing.
- For multi-agent sessions, include relevant Codex subagent or background-thread logs modified near the main log timestamp when those logs are available.

## Runtime operations

- Ignore Claude Code `allowed-tools` frontmatter when Codex does not support it; rely on the active Codex tool list.
- Parallel insight extraction: if a Codex subagent tool such as `spawn_agent` is available through normal tool discovery, use it to run each hunter prompt from `agents/`. If no subagent tool is available, run the hunter prompts in the current context and preserve the same FINDING block output.
- User decisions: translate `AskUserQuestion` blocks to `request_user_input` when available, or ask in chat. When a preview is needed and the input tool does not support preview fields, show the preview in chat immediately before the question.
- Task tracking: translate `TaskCreate`, `TaskList`, and `TaskUpdate` usage to `update_plan`; keep one item per selected finding and only one item `in_progress` at a time.
