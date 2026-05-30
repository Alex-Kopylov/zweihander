# adapt-skill-for-ai-harness

This skill maintains the AI Assistant Harness Adaptation policy for explicitly named target skills.

The shared `SKILL.md` stays Claude Code-baseline. Host-specific wording, tool names, command names, and workflow details belong in metadata-linked files under `references/ai-assistant-harnesses/`.

Claude Code and Codex tool surfaces are moving targets. When a harness reference contains researched tool names, command names, or version-sensitive behavior, include:

- `Checked: YYYY-MM-DD`
- Source links to the official product documentation used for that check
- A narrow note about what changed if the update is a follow-up

Future harness updates should happen through focused PRs that update the relevant harness reference and any static tests or evals that guard the behavior.
