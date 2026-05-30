# Live Lab Protocol

Use this protocol to manually verify the action matrix and an already-adapted target skill. The first version covers only Claude Code and Codex personas.

## Matrix Setup

Check this skill has:

- `metadata.ai-assistant-harness-adaptation.action-matrix`
- `references/harness-action-matrix.json`
- No local `references/ai-assistant-harnesses/claude-code.md`
- No local `references/ai-assistant-harnesses/codex.md`

Run:

```shell
python plugins/ai-assistant-ops/skills/adapt-skill-for-ai-harness/scripts/lookup_harness_action.py --action CreateAgent --assistant Codex
```

Expected pass condition: the output is JSON for the `CreateAgent`/`Codex` entry and includes Codex-specific terms such as `spawn_agent`.

## Target Skill Setup

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

Fail the lab if this skill grows its own per-harness markdown references, a matrix lookup fails, a persona reads both target harness files, a persona reads the wrong target harness file, or the target `SKILL.md` relies on a shared cross-harness instruction table.
