# Codex Harness Notes

Codex-specific behavior for this workflow:

- User decisions: use `request_user_input` when a bounded selection or clarification is needed; use normal chat when a tool call is unnecessary or unavailable.
- Reply and commit steps: use the matching available Codex skills (`$dev-workflow:pr-comment`, `$dev-workflow:commit`), loading their `SKILL.md` files if the current turn requires them.
- Delegation: use a subagent mechanism only when the active tool list provides one; otherwise handle the investigation in the current context.
