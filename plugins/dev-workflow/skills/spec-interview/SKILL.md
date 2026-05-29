---
name: spec-interview
description: Use when the user wants an in-depth requirements interview that produces a detailed implementation spec.
metadata:
  codex-read-it: reference/codex.md
  claude-code-read-it: reference/claude-code.md
---

# Spec Interview

Interview the user in depth about technical implementation, API design, data models, prompt engineering pitfalls, LLM output quality, and tradeoffs. Ask non-obvious follow-up questions, track contradictions, and resolve them before writing the spec.

If harness-specific tool mapping is needed, load exactly one matching `metadata.*-read-it` reference; otherwise load none.

Write the final spec only after the requirements are stable.
