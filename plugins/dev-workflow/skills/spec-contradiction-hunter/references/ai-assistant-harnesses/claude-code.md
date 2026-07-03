# Claude Code Harness Notes

Use this file only when the active harness is Claude Code.

- Use `AskUserQuestion` when the skill says to ask the user for missing material, confirmations, clarifications, or resolutions.
- Use the `Agent` tool for contradiction hunters. Launch all applicable agents in a single assistant message when the tool interface allows parallel dispatch.
- For domain-specific contradiction hunters, use a `general-purpose` agent with `model: "opus"` and a prompt tailored to the domain.
