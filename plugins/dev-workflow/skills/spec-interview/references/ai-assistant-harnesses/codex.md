# Codex

Use these mappings only when this skill needs harness-specific tooling:

- For bounded clarification, use `request_user_input` when available; otherwise ask in chat.
- For file inspection, use `sed`, `nl`, or `exec_command` with scoped reads.
- For creating or updating a spec file, use `apply_patch` for manual edits; use formatters only for mechanical rewrites.
