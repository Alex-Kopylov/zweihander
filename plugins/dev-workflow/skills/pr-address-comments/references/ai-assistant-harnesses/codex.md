# Codex Harness Notes

Translate only the shared workflow terms needed for Codex execution.

- Treat `AskUserQuestion` as `request_user_input` when a bounded selection or clarification is needed; use normal chat when a tool call is unnecessary or unavailable.
- Treat `Skill(dev-workflow:pr-comment)` and `Skill(dev-workflow:commit)` as instructions to use the matching available Codex skills, loading their `SKILL.md` files if the current turn requires them.
- Treat `Agent` as optional subagent delegation. Use it only when the active Codex tool list or discovered tools provide an allowed subagent mechanism, and otherwise handle the investigation in the current context.
