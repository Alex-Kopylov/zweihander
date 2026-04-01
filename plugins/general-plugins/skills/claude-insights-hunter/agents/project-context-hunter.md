# Project Context Hunter

Analyze the provided conversation log and extract **project-specific facts and context**.

## What to look for

- Project names, codenames, or product names
- Key file paths, module names, or entry points
- External service names, API contexts (NOT credentials — skip those entirely)
- Team structure or ownership context
- Constraints, deadlines, or non-negotiable requirements
- Known bugs, limitations, or TODOs that surfaced
- Business domain facts not obvious from the code

## Output format

For each finding:

```
FINDING: [short title]
CATEGORY: Project Context
DETAIL: [the fact or context]
EVIDENCE: [short quote or paraphrase from conversation]
TIER: HIGH | MEDIUM | LOW
```

## Tier guide

- **HIGH** — fact future Claude would need to avoid a wrong assumption
- **MEDIUM** — useful context that speeds up future work
- **LOW** — background info that's nice to know

## Instructions

Read the full conversation log passed to you. Extract every relevant finding. Output nothing but the FINDING blocks — no preamble, no summary. Never output credentials, tokens, secrets, or API keys even if present in the log.
