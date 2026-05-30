---
name: adapt-skill-for-ai-harness
description: "Use when adapting skills for AI Assistant Harness Adaptation, making explicitly named skills harness-agnostic, or moving Claude Code and Codex-specific instructions into metadata-linked reference files."
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Adapt Skill For AI Harness

These metadata keys point to this skill's per-harness notes:

```yaml
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
```

Read them this way: identify the active assistant harness, choose that one metadata value, load exactly one matching metadata-linked harness reference when harness-specific tool or command mapping is needed, and skip the other harness files unless the user explicitly asks to edit or compare them.

## Purpose

Adapt only an explicitly named target skill or target skill path so its shared `SKILL.md` stays Claude Code-baseline while assistant-specific instructions move into metadata-linked files under `references/ai-assistant-harnesses/`.

Do not migrate every skill in a repository unless the user explicitly asks for that broader migration.

## Adaptation Policy

Use Claude Code format, wording, and tool names as the baseline in shared `SKILL.md` content.

Add the flat, unique metadata keys shown above, one per supported harness.

Store only file links in metadata values. Do not store tool mappings, prose policy, compatibility notes, or lists of all harness instructions in metadata.

Store harness adaptation files under `references/ai-assistant-harnesses/<harness-id>.md`. The first supported harnesses are `claude-code` and `codex`.

The adapted target `SKILL.md` must tell assistants to identify the active harness, load exactly one matching metadata-linked harness reference when harness-specific adaptation is needed, and skip non-matching harness files.

Do not create a shared cross-harness instruction table or a full list of all assistant harness instructions in the shared `SKILL.md`.

## Workflow

1. Resolve the explicitly named target skill directory or path. If the user did not name one target skill, ask for the target before editing.
2. Inspect only files that can enter LLM tool-call invocation context: `SKILL.md`, files under `references/`, files under `agents/`, examples, assets that are directly loaded or described to the model, scripts referenced by the skill, and similar explicitly loaded files.
3. Ignore README files, tests, docs, generated artifacts, and development-only support files unless the target skill says to load them during normal invocation.
4. Detect explicit harness wording, tool names, command names, command-like workflow references, and host-specific instructions.
5. Preserve Claude Code as the shared baseline. Keep broadly valid skill workflow in `SKILL.md`.
6. Move Codex-specific instructions to `references/ai-assistant-harnesses/codex.md`.
7. Move Claude Code-specific details that should not stay in shared prose to `references/ai-assistant-harnesses/claude-code.md`.
8. If per-assistant instructions already exist, reorganize them into this `references/ai-assistant-harnesses/` format and remove duplicated old adaptation information.
9. Add or update the flat metadata links in the target `SKILL.md`.
10. Add or update focused static tests or evals when the repository has a test/eval convention that can enforce the policy.
11. Report the exact files changed and the verification commands run.

## Harness References

Load only the active harness reference when you need host-specific wording:

- For Claude Code, use `references/ai-assistant-harnesses/claude-code.md`.
- For Codex, use `references/ai-assistant-harnesses/codex.md`.

Keep these files narrow. They are not general docs for the target skill; they only hold the host-specific adaptations needed to keep shared skill content harness-agnostic.

## Safety Rules

Do not batch-migrate unrelated skills.

Do not rewrite README, tests, docs, or catalog text while adapting a target skill unless the user-facing catalog or verification changes require it.

Do not load other harness references while acting as a specific harness.

Do not leave both old per-assistant instructions and new metadata-linked harness files active for the same behavior.

Do not replace the Claude Code-baseline shared workflow with Codex wording. Put Codex wording in `codex.md`.

## Verification

For each adapted target, check that:

- `SKILL.md` has only flat `metadata.ai-assistant-harness-adaptation.*` links.
- Every metadata value ends in `.md` and resolves under `references/ai-assistant-harnesses/`.
- The target instructs assistants to load exactly one matching metadata-linked harness reference.
- The target has no shared table or complete shared list of all harness instructions.
- Only explicitly requested target skills changed.

Run the repository's relevant static tests, eval checks, JSON validation, and Markdown whitespace checks before finishing.
