# Writing Conventions

Instruction-file conventions adapted for use here.

## Diff block header

Use `**Why this helps:**` instead of `**Why:**` so the reason is clear when read later.

```
### Update: ./AGENTS.md
**Why this helps:** [one-line reason a future session benefits from this]

\`\`\`diff
+ [addition]
\`\`\`
```

## Inline command format

When storing bash commands or CLI workflows in an instruction file, prefer:

```
`<command>` - <brief description>
```

Example:
```
`uv run pytest -x` - run tests, stop on first failure
`uv run ty check` - type-check the project
```

One command per line. Description after the dash, lowercase, no period.

## Pre-write checklist

Before writing, verify each addition:

- Is it project-specific? (not generic advice)
- Would a new AI Assistant session actually find this useful?
- Is this the most concise way to say it?
- Are file paths and commands accurate?
