# Live Lab Protocol

Use this protocol to manually verify an already-adapted target skill. The first version covers only Claude Code and Codex personas.

## Setup

Select one adapted target skill that has:

- A shared `SKILL.md`
- `metadata.ai-assistant-harness-adaptation.claude-code`
- `metadata.ai-assistant-harness-adaptation.codex`
- `references/ai-assistant-harnesses/claude-code.md`
- `references/ai-assistant-harnesses/codex.md`

Start each persona in a clean session or clean sub-session with access to the same target skill files.

## Claude Code Persona Prompt

```text
Invoke the adapted target skill at <target-skill-path> without taking actions.
Report which files you read or loaded to understand the skill.
Stop after reporting the loaded files.
```

Expected pass condition: the persona reads the target `SKILL.md` and only `references/ai-assistant-harnesses/claude-code.md` from the harness directory.

## Codex Persona Prompt

```text
Invoke the adapted target skill at <target-skill-path> without taking actions.
Report which files you read or loaded to understand the skill.
Stop after reporting the loaded files.
```

Expected pass condition: the persona reads the target `SKILL.md` and only `references/ai-assistant-harnesses/codex.md` from the harness directory.

## Record

For each persona, record:

- Date
- Persona and product version when available
- Target skill path
- Files read or loaded
- Pass or fail
- Notes about unexpected context loading

Fail the lab if a persona reads both harness files, reads the wrong harness file, or relies on a shared cross-harness instruction table in the target `SKILL.md`.
