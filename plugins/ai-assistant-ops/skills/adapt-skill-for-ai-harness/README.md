# adapt-skill-for-ai-harness

This skill maintains the AI Assistant Harness Adaptation policy for explicitly named target skills.

`references/harness-action-matrix.json` is the scriptable source of truth for translating shared workflows, skills, tools, and commands across harnesses. Lookups are action-first, then assistant: `matrix["actions"]["CreateAgent"]["Codex"]`.

End-result target skills can still use metadata-linked files under `references/ai-assistant-harnesses/` when host-specific wording, tool names, command names, and workflow details need to stay out of shared `SKILL.md`.

Claude Code and Codex tool surfaces are moving targets. When the matrix or a target harness reference contains researched names or version-sensitive behavior, include:

- `Checked: YYYY-MM-DD`
- Source links to the official product documentation used for that check
- A narrow note about what changed if the update is a follow-up

Update harnesses through focused PRs that update the matrix, affected target harness references, and static tests or evals guarding the behavior.
