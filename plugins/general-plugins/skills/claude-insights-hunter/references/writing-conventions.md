# Writing Conventions

Conventions from Anthropic's `claude-md-management` plugin, adapted for use here.

## Diff block header

Use `**Why this helps:**` (not just `**Why:**`) — the longer form is clearer when
someone reads the file cold and needs context on why a line was added.

```
### Update: ./CLAUDE.md
**Why this helps:** [one-line reason a future session benefits from this]

\`\`\`diff
+ [addition]
\`\`\`
```

## Inline command format

When storing bash commands or CLI workflows in a CLAUDE.md, prefer:

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

Before finalising what gets written, verify each addition:

- Is it project-specific? (not generic advice)
- Would a new Claude session actually find this useful?
- Is this the most concise way to say it?
- Are file paths and commands accurate?
