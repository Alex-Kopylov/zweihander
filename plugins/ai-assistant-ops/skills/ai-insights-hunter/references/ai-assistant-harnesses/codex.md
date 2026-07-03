# Codex Harness Adaptation

Use this file only when the active harness is Codex.

## Conversation logs

- Prefer an explicit user-provided log path. Otherwise search Codex session logs under `~/.codex/sessions/` for recent `.jsonl` files that match the current project path or session timing.
- For multi-agent sessions, include relevant Codex subagent or background-thread logs modified near the main log timestamp when those logs are available.

## Runtime operations

- Delegation: use a subagent tool such as `spawn_agent` when available;
  otherwise run the hunter prompts in the current context and preserve the same
  FINDING block output.
- User decisions: use `request_user_input` when available; otherwise ask in
  chat. When a preview is needed and the input tool does not support preview
  fields, show the preview in chat immediately before the question.
- Task tracking: use `update_plan`; keep one item per selected finding and only one item `in_progress` at a time.
- Skill invocation: use `$ai-assistant-ops:agents-md-improver` or load the
  skill's `SKILL.md`.
