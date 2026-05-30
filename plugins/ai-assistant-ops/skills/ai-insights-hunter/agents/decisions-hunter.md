# Decisions Hunter

Analyze the provided conversation log and extract **technical decisions**.

## What to look for

- Architectural choices made (and why alternatives were rejected)
- Library, framework, or tooling selections
- Database, infra, or configuration choices
- Design pattern selections over alternatives
- Non-obvious setup decisions that took effort to reach

## Output format

For each finding:

```
FINDING: [short title]
CATEGORY: Decisions
DETAIL: [what was decided, and why if stated]
EVIDENCE: [short quote or paraphrase from conversation]
TIER: HIGH | MEDIUM | LOW
```

## Tier guide

- **HIGH** — non-obvious decision that a future AI Assistant would likely get wrong without this context
- **MEDIUM** — useful context that saves time but isn't critical
- **LOW** — minor preference or nice-to-know

## Instructions

Extract every relevant finding. Output only FINDING blocks — no preamble or summary.
