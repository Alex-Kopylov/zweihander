# Codex Harness Notes

Use this file only when the active harness is Codex.

- Ask the user in chat for missing material, confirmations, clarifications, or resolutions. Use `request_user_input` only when it is available and a bounded structured choice is better than plain chat.
- Treat the active user request as the topic or material to analyze; Codex may not expand `$ARGUMENTS`.
- If `tool_search` is available, use it to discover a subagent capability such as `spawn_agent`.
- If a subagent capability is available and current harness instructions permit it, use it for the contradiction hunters and keep the same analytical lenses from the shared process.
- If no subagent capability is available, run the analytical lenses directly in the current response rather than naming unavailable tools.
