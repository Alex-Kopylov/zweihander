# Codex Harness

Codex-specific behavior for this workflow:

- Use `request_user_input` for bounded item decisions when available; otherwise
  ask in chat.
- `request_user_input` options support labels and descriptions. Present proposed
  code/config previews in chat before the request, or fold brief previews into
  the option description.
