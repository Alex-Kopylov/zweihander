# Skill `description` Frontmatter

The host reads only `name` and `description` to decide whether to load a skill,
and shortens descriptions when many skills are installed. Write it in this
order:

1. **What and for which case.** One short third-person clause naming what the
   skill does and its key use case, so it survives truncation.
2. **When.** `Use when …`, with the situations and specific domain terms a
   user would actually say.
3. **Boundary.** `Not for …`, only where a near-miss request could plausibly
   trigger it. Anchor generic phrases to the domain ("check this CV before I
   apply", not "final check").

Leave out:

- Implementation detail: which files it writes, which tools it runs, which
  skill it chains into. The body owns the process.
- `$skill-name` as a trigger; the harness already invokes the
  skill by that name. This bans it only in `description`: a skill's body and
  references may name other skills it deliberately invokes.
- XML tags and angle brackets.

Length: 1–1024 characters.

**User-only skills** (`policy.allow_implicit_invocation: false` in
`agents/openai.yaml`) are never model-selected. Only a person reads their
description, so it says what the skill does; drop the `Use when …` and
`Not for …` parts.

Sources: [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices),
[agentskills.io specification](https://agentskills.io/specification),
[OpenAI: build skills](https://learn.chatgpt.com/docs/build-skills).
