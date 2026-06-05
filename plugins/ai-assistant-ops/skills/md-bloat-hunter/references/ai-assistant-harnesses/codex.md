# Codex Harness

Use this file only when the active harness is Codex.

- User approval questions: use `request_user_input` when available and the
  current mode permits it; otherwise ask in chat and wait.
- Detector dispatch: use `tool_search` to expose deferred multi-agent tools
  when needed, then use `spawn_agent` to spawn all selected detector agents in
  one batch when that tool is available and current harness instructions permit
  subagents.
- Wait for every spawned agent before reducing findings.
- Use `multi_tool_use.parallel` only for independent developer tool calls; it
  is not a substitute for detector-agent delegation.
