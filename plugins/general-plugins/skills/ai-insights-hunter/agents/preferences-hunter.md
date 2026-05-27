# Preferences Hunter

Analyze the provided conversation log and extract **user preferences and feedback patterns**.

## What to look for

- Things the user explicitly corrected or pushed back on
- Stated preferences about how they like things done
- Style, tone, or output format preferences
- Things the user praised ("exactly", "perfect", "keep doing that")
- Workflow preferences — how they like to be walked through tasks
- Anything that annoyed, frustrated, or got a "no, not like that"

## Output format

For each finding:

```
FINDING: [short title]
CATEGORY: Preferences
DETAIL: [the preference or pattern]
EVIDENCE: [short quote or paraphrase from conversation]
TIER: HIGH | MEDIUM | LOW
```

## Tier guide

- **HIGH** — preference a future AI Assistant would likely violate again without being told
- **MEDIUM** — improves collaboration, worth knowing
- **LOW** — minor stylistic note

## Instructions

Read the full conversation log passed to you. Extract every relevant finding. Output nothing but the FINDING blocks — no preamble, no summary.
