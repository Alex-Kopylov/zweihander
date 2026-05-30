# adapt-skill-for-ai-harness

This skill maintains the AI Assistant Harness Adaptation policy for explicitly named target skills.

This skill uses `references/harness-action-matrix.json` as the scriptable source of truth for translating shared workflows, skills, tools, and commands across harnesses. Lookups are action-first, then assistant, such as `matrix["actions"]["CreateAgent"]["Codex"]`.

End-result target skills can still use metadata-linked files under `references/ai-assistant-harnesses/` when host-specific wording, tool names, command names, and workflow details need to stay out of shared `SKILL.md`.

Claude Code and Codex tool surfaces are moving targets. When the matrix or a target harness reference contains researched names or version-sensitive behavior, include:

- `Checked: YYYY-MM-DD`
- Source links to the official product documentation used for that check
- A narrow note about what changed if the update is a follow-up

Future harness updates should happen through focused PRs that update the matrix, any affected target harness references, and any static tests or evals that guard the behavior.
