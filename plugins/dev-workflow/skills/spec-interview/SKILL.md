---
name: spec-interview
description: Use when the user wants an in-depth requirements interview that produces a detailed implementation spec.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Spec Interview

Interview the user in depth about technical implementation, API design, data models, prompt engineering pitfalls, LLM output quality, and tradeoffs. Ask non-obvious follow-up questions, track contradictions, and resolve them before writing the spec.

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

Write the final spec only after the requirements are stable.
