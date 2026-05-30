---
name: adapt-skill-for-ai-harness
description: "Use when adapting skills for AI Assistant Harness Adaptation, using an assistant harness action matrix, or making explicitly named target skills harness-agnostic."
metadata:
  ai-assistant-harness-adaptation.action-matrix: references/harness-action-matrix.json
---

# Adapt Skill For AI Harness

This skill adapts an explicitly named target skill from one AI assistant harness vocabulary to another.

Its reusable source of truth is an assistant harness action matrix, not per-harness explanatory notes for this skill itself.

```python
matrix = load_json(metadata["ai-assistant-harness-adaptation.action-matrix"])
entry = matrix["actions"][action_key][assistant_key]
codex_agent = matrix["actions"]["CreateAgent"]["Codex"]
```

Use `scripts/lookup_harness_action.py --action CreateAgent --assistant Codex` when scriptable lookup is useful.

## Purpose

Adapt only an explicitly named target skill or target skill path. Do not migrate every skill in a repository unless the user explicitly asks for that broader migration.

The matrix maps workflows, skills, tools, and commands that different AI harnesses share in purpose but name differently. It should capture names, aliases, surfaces, discovery paths, and short nuances needed for translation. It should not explain a harness to itself.

End-result target skills may still receive `references/ai-assistant-harnesses/claude-code.md` and `references/ai-assistant-harnesses/codex.md` when that is the right way to keep target-specific wording out of shared `SKILL.md`.

## Target Adaptation Policy

Use Claude Code format, wording, and tool names as the baseline in shared target `SKILL.md` content.

For target skills, add flat metadata links, one per supported harness:

```yaml
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
```

Store only file links in metadata values. Do not store tool mappings, prose policy, compatibility notes, or lists of all harness instructions in metadata.

Store target harness adaptation files under `references/ai-assistant-harnesses/<harness-id>.md`. Keep them narrow and include only the actions that target skill actually needs.

The adapted target `SKILL.md` must tell assistants to identify the active harness, load exactly one matching metadata-linked harness reference when harness-specific adaptation is needed, and skip non-matching harness files.

Do not create a shared cross-harness instruction table or a full list of all assistant harness instructions in the shared target `SKILL.md`.

Do not create `references/ai-assistant-harnesses/` inside this skill. That directory is an output pattern for adapted target skills.

## Workflow

1. Resolve the explicitly named target skill directory or path. If the user did not name one target skill, ask for the target before editing.
2. Load `references/harness-action-matrix.json` when harness-specific mappings are needed.
3. Inspect only files that can enter LLM invocation context: `SKILL.md`, files under `references/`, files under `agents/`, examples, assets directly loaded or described to the model, scripts referenced by the skill, and similar explicitly loaded files.
4. Ignore README files, tests, docs, generated artifacts, and development-only support files unless the target skill says to load them during normal invocation.
5. Detect explicit harness wording, tool names, command names, command-like workflow references, and host-specific instructions.
6. Map each host-specific operation to an action key such as `CreateAgent`, `AskUser`, `TrackTasks`, `EditFile`, or `SlashCommand`.
7. For each pair, look up `matrix["actions"][action_key][assistant_key]`; for example, use `matrix["actions"]["CreateAgent"]["Codex"]`.
8. Preserve Claude Code as the shared baseline. Keep broadly valid skill workflow in the target `SKILL.md`.
9. Move Codex-specific instructions to the target `references/ai-assistant-harnesses/codex.md`.
10. Move Claude Code-specific details that should not stay in shared prose to the target `references/ai-assistant-harnesses/claude-code.md`.
11. If per-assistant instructions already exist, reorganize them into the target `references/ai-assistant-harnesses/` format and remove duplicated old adaptation information.
12. Add or update the flat metadata links in the target `SKILL.md`.
13. Add or update focused static tests or evals when the repository has a test/eval convention that can enforce the policy.
14. Report the exact files changed and the verification commands run.

## Matrix Maintenance

Keep action keys stable and TitleCase. Keep assistant keys stable and product-oriented, currently `ClaudeCode` and `Codex`.

Each action must have a `kind` value: `workflow`, `skill`, `tool`, or `command`.

Prefer compact fields:

- `surface`: where the concept appears, such as `tool`, `skill`, `slash-command`, or `workflow`.
- `terms`: current names the harness uses.
- `aliases`: older or alternate names.
- `discovery`: how to find deferred or optional capabilities.
- `nuances`: short compatibility notes that matter during translation.

Preserve `lookup_order: ["action", "assistant"]` so scripts can keep using `matrix["actions"][action_key][assistant_key]`.

## Safety Rules

Do not batch-migrate unrelated skills.

Do not rewrite README, tests, docs, or catalog text while adapting a target skill unless the user-facing catalog or verification changes require it.

Do not load other target harness references while acting as a specific harness.

Do not leave both old per-assistant instructions and new metadata-linked harness files active for the same behavior.

Do not replace the Claude Code-baseline shared workflow with Codex wording. Put Codex wording in the target `codex.md`.

## Verification

For each adapted target, check that:

- `SKILL.md` has only flat `metadata.ai-assistant-harness-adaptation.*` links.
- Every metadata value ends in `.md` and resolves under `references/ai-assistant-harnesses/`.
- The target instructs assistants to load exactly one matching metadata-linked harness reference.
- The target has no shared table or complete shared list of all harness instructions.
- Only explicitly requested target skills changed.

For this skill itself, check that:

- `metadata.ai-assistant-harness-adaptation.action-matrix` resolves to `references/harness-action-matrix.json`.
- `matrix["actions"][action_key][assistant_key]` lookup works for at least `CreateAgent` and `Codex`.
- This skill does not ship its own `references/ai-assistant-harnesses/claude-code.md` or `references/ai-assistant-harnesses/codex.md`.

Run the repository's relevant static tests, eval checks, JSON validation, and Markdown whitespace checks before finishing.
