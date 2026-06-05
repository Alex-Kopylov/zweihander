# Codex Harness Notes

Use this file only when Codex is the active assistant harness.

## AskUser

For `AskUserQuestion` prompts in the shared workflow, use `request_user_input` when a bounded choice UI is available. If `request_user_input` is unavailable or mode-limited, ask in chat and wait for the answer.

Ask before installing or updating `@mermaid-js/mermaid-cli`; do not auto-update Mermaid CLI.
