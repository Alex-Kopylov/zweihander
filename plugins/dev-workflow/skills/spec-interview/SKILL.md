---
name: spec-interview
description: Use when the user wants an in-depth requirements interview that produces a detailed implementation spec.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Spec Interview

Interview the user in depth about technical implementation, API design, data models, prompt engineering pitfalls, LLM output quality, and tradeoffs. Ask non-obvious follow-up questions, track contradictions, and resolve them before writing the spec.

Identify the active AI assistant harness before using harness-specific tool mapping. If harness-specific adaptation is needed, load exactly one matching metadata-linked harness reference for the active harness. Skip all non-matching harness files. If no harness-specific adaptation is needed, load none.

Write the final spec only after the requirements are stable.
