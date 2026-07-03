---
name: adapt-skill-for-ai-harness
description: "Use when adapting skills for AI Assistant Harness Adaptation, using an assistant harness action matrix, or making explicitly named target skills harness-agnostic."
metadata:
  ai-assistant-harness-adaptation.action-matrix: references/harness-action-matrix.json
---

# Adapt Skill For AI Harness

This skill adapts an explicitly named target skill from one AI assistant harness vocabulary to another.

The assistant harness action matrix is the reusable source of truth, not per-harness explanatory notes for this skill.

```python
matrix = load_json(metadata["ai-assistant-harness-adaptation.action-matrix"])
entry = matrix["actions"][action_key][assistant_key]
codex_agent = matrix["actions"]["CreateAgent"]["Codex"]
```

Use `scripts/lookup_harness_action.py --action CreateAgent --assistant Codex` for scriptable lookup.

## Purpose

Adapt only an explicitly named target skill or target skill path. Do not migrate every skill in a repository unless the user explicitly asks for that broader migration.

The matrix maps shared-purpose workflows, skills, tools, and commands that AI harnesses name differently. It should capture names, aliases, surfaces, discovery paths, and short translation nuances, not explain a harness to itself.

Adapted target skills may still receive `references/ai-assistant-harnesses/claude-code.md` and `references/ai-assistant-harnesses/codex.md` when that keeps target-specific wording out of shared `SKILL.md`.

## Target Adaptation Policy

Shared target `SKILL.md` content is harness-agnostic. It names no harness and no harness's mechanism tools. It states intent in generalized language: "ask the user (bounded options)", "invoke the `plugin-name:skill-name` skill", "delegate to the `plugin-name:agent-name` agent", "track the work as plan items". Slash commands are treated as regular skills and referenced the same generalized way. Trigger phrases inside frontmatter `description` fields are exempt. One harness's dialect in shared prose forces every other harness to translate and leaks foreign names into references; agnostic wording removes the translation step entirely.

Adapted skills carry no `allowed-tools` frontmatter; delete the key when adapting.

The actor is "the AI agent" or "you". "Harness" refers only to the surrounding CLI/runtime infrastructure and appears in shared target content only in the standard Harness Adaptation wording and metadata keys. This skill itself is the documented exception and may discuss harnesses freely.

For target skills, add flat metadata links, one per supported harness:

```yaml
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
```

Metadata values must be file links only. Do not store tool mappings, prose policy, compatibility notes, or lists of all harness instructions there.

Store target harness adaptation files under `references/ai-assistant-harnesses/<harness-id>.md`. Keep them narrow and include only actions the target skill needs.

Never instruct baseline capabilities. Every harness reads, searches, creates, edits, and writes files and runs shell commands natively with its own tools (`Read`, `Grep`, `Glob`, `Bash`, `Write`, `Edit`, `MultiEdit`, `exec_command`, `apply_patch`, `sed`, `nl`, `rg`, and similar). Assistants handle these unaided; telling them which of their own basic tools to use only pollutes context. Do not write harness-reference instructions for these actions and do not translate them between harnesses. Matrix actions marked `"adaptation": "baseline"` exist for lookup completeness and never become reference content.

Map only differently named shared mechanisms where an explicit nudge changes behavior, marked `"adaptation": "map"` in the matrix: asking the user (`AskUserQuestion` / `request_user_input`), subagent delegation (`Agent` / `spawn_agent`), skill and slash-command invocation (`Skill(...)` and `/plugin-name:skill-name` / `$plugin-name:skill-name`), task tracking (`TaskCreate` / `update_plan`), and harness-specific facts such as context-file or storage locations. For every mapped mechanism the target workflow uses, each supported harness's reference carries the nudge in its own vocabulary: `AskUserQuestion` in `claude-code.md` / `request_user_input` in `codex.md`; `Agent` / `spawn_agent`; `Skill(plugin:skill)` / `$plugin:skill`; `TaskCreate` / `update_plan`. References carry no general instructions; anything harness-independent belongs in the shared `SKILL.md`.

A capability gap never licenses tool coaching. When a harness genuinely cannot perform a workflow step natively, state the gap as a fact only if it changes the workflow, and never name specific tools or commands to work around it — the AI agent picks its own workaround.

Write each harness reference purely in its own harness's vocabulary. A harness reference must never name another harness or another harness's tools, frontmatter keys, or invocation syntax, and must never use translate-from framing such as "treat X as Y" or "translate X to Y". Anchor each instruction on the workflow action it adapts — asking the user, task tracking, delegation, skill invocation — stated directly in the target harness's own terms. Tokens quoted from the shared skill text (such as `$plugin-name:skill-name` invocation strings) are allowed anchors when the mapping needs them.

Exception: when a tool surface is the target skill's subject matter — a task-management skill teaching task tools, for example — treat that surface as skill content, not harness adaptation.

If nothing non-baseline remains for a harness, do not create that harness reference file or its metadata link. A target skill whose workflow needs no mechanism mapping needs no harness adaptation at all. Do not create a harness reference that only restates the shared baseline.

The adapted target `SKILL.md` must contain this exact harness adaptation wording, and nothing more about harness selection:

```markdown
## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.
```

Keep the block tiny. When a target skill states the instruction as a bare intro paragraph instead of a section, use the same single sentence without the heading. Do not add harness-identification steps, baseline-fallback sentences, or per-harness explanations around it.

Do not create a shared cross-harness instruction table or a full list of all assistant harness instructions in the shared target `SKILL.md`.

Do not create `references/ai-assistant-harnesses/` inside this skill. That directory is an output pattern for adapted target skills.

## Workflow

1. Resolve the explicitly named target skill directory or path. If the user did not name one target skill, ask for the target before editing.
2. Load `references/harness-action-matrix.json` when harness-specific mappings are needed.
3. Inspect only files that can enter LLM invocation context: `SKILL.md`, files under `references/`, files under `agents/`, examples, assets directly loaded or described to the model, scripts referenced by the skill, and similar explicitly loaded files.
4. Ignore README files, tests, docs, generated artifacts, and development-only support files unless the target skill says to load them during normal invocation.
5. Detect explicit harness wording, tool names, command names, command-like workflow references, and host-specific instructions.
6. Map each host-specific operation to an action key such as `CreateAgent`, `AskUser`, `TrackTasks`, or `SlashCommand`. Drop operations whose matrix action is marked `"adaptation": "baseline"`; remove baseline tool coaching from adaptation output instead of translating it.
7. For each remaining pair, look up `matrix["actions"][action_key][assistant_key]`; for example, use `matrix["actions"]["CreateAgent"]["Codex"]`.
8. Make the shared target `SKILL.md` harness-agnostic; keep all broadly valid workflow there.
9. Move Codex-specific instructions to the target `references/ai-assistant-harnesses/codex.md`.
10. Move Claude Code-specific details to the target `references/ai-assistant-harnesses/claude-code.md`.
11. If per-assistant instructions exist, reorganize them into the target `references/ai-assistant-harnesses/` format and remove duplicated old adaptation information.
12. Add or update the flat metadata links in the target `SKILL.md`.
13. Encode every policy decision from the adaptation as a focused static test or eval when the repository has that convention. Prose-only policy regresses on the next edit; a failing test does not.
14. Report the exact files changed and the verification commands run.

## Matrix Maintenance

Keep action keys stable and TitleCase. Keep assistant keys stable and product-oriented, currently `ClaudeCode` and `Codex`.

Each action must have a `kind` value: `workflow`, `skill`, `tool`, or `command`.

Prefer compact fields:

- `adaptation`: `map` for shared mechanisms worth explicit per-harness instructions; `baseline` for native capabilities that must never generate them.
- `surface`: where the concept appears, such as `tool`, `skill`, `slash-command`, or `workflow`.
- `terms`: current names the harness uses.
- `aliases`: older or alternate names.
- `discovery`: how to find deferred or optional capabilities.
- `nuances`: short compatibility notes that matter during translation.

For `InvokeSkill`, keep user-facing direct-invocation forms explicit: Codex uses `$skill-name` or `$plugin-name:skill-name`; Claude Code uses `/skill-name` or `/plugin-name:skill-name`, while `Skill(name)` or `Skill(plugin-name:skill-name)` is Claude Code tool and permission syntax for model-driven invocation.

Preserve `lookup_order: ["action", "assistant"]` so scripts can keep using `matrix["actions"][action_key][assistant_key]`.

## Safety Rules

Do not batch-migrate unrelated skills.

Do not rewrite README, tests, docs, or catalog text while adapting a target skill unless the user-facing catalog or verification changes require it.

Do not load other target harness references while acting as a specific harness.

Do not leave both old per-assistant instructions and new metadata-linked harness files active for the same behavior.

Shared workflow content names no harness's mechanisms; each harness's wording lives only in its own reference file.

## Verification

For each adapted target, check that:

- `SKILL.md` has only flat `metadata.ai-assistant-harness-adaptation.*` links.
- Every metadata value ends in `.md` and resolves under `references/ai-assistant-harnesses/`.
- Shared content is harness-agnostic: no harness names or mechanism tool names outside frontmatter `description` fields.
- No `allowed-tools` frontmatter remains.
- The target contains the exact standard harness adaptation wording and nothing more about harness selection.
- The target has no shared table or complete shared list of all harness instructions.
- Harness references contain no baseline-capability coaching: no instructions naming which file read, search, edit, write, or shell tools to use.
- Harness references never name another harness or another harness's tool vocabulary.
- Every harness reference carries at least one mapped mechanism, harness-specific fact, or compatibility nuance; contentless references are removed along with their metadata links.
- Only explicitly requested target skills changed.

For this skill itself, check that:

- `metadata.ai-assistant-harness-adaptation.action-matrix` resolves to `references/harness-action-matrix.json`.
- `matrix["actions"][action_key][assistant_key]` lookup works for at least `CreateAgent` and `Codex`.
- This skill does not ship its own `references/ai-assistant-harnesses/claude-code.md` or `references/ai-assistant-harnesses/codex.md`.

Run the repository's relevant static tests, eval checks, JSON validation, and Markdown whitespace checks before finishing.
