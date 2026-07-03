# Claude Code Harness Notes

Use this file only when the active harness is Claude Code.

- User decisions: use `AskUserQuestion` when the workflow needs missing material, confirmations, clarifications, or resolutions.
- Delegation: use the `Agent` tool. Launch all applicable agents in a single assistant message when the tool interface allows parallel dispatch.
- Domain-specific delegation: use a `general-purpose` agent with `model: "opus"` and a prompt tailored to the domain.
