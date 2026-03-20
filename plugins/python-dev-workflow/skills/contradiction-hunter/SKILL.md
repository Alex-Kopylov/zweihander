---
argument-hint: [topic or paste the information to analyze]
name: contradiction-hunter
description: This skill should be used when the user wants to "find contradictions", "check consistency", "validate my spec", "cross-check requirements", "spot inconsistencies", or has provided a body of information (spec, requirements, design doc) that needs consistency validation. Spawns parallel agents to hunt obvious and deeper contradictions.
allowed-tools: AskUserQuestion, Write, Read, TeamCreate, Agent
---

# Contradiction Hunter

Analyze user-provided information for internal contradictions, inconsistencies, and logical conflicts. Operate by dispatching 2-3 parallel agents, each with a different analytical lens, then synthesize findings.

## Process

### Step 1: Gather Information

If the user has not yet provided the information to analyze, use **AskUserQuestion** to ask them to paste or describe the material (spec, requirements, design decisions, constraints, etc.). Keep asking follow-up questions until there is a substantial body of claims to analyze.

### Step 2: Dispatch Parallel Contradiction Hunters

Launch **all agents simultaneously** in a single message. Each agent receives the full collected information and a specific hunting mandate:

**Agent 1 — Surface Contradictions**
Hunt for obvious, direct contradictions: statements that explicitly conflict with each other. Examples: "must use REST" vs "uses GraphQL", "no auth required" vs "JWT tokens for all endpoints", conflicting data types for the same field, mutually exclusive requirements.

**Agent 2 — Structural & Logical Contradictions**
Hunt for deeper inconsistencies that aren't direct word-for-word conflicts: requirements that are technically incompatible (e.g., "real-time" + "batch processing only"), scope mismatches (feature described in overview but absent from detailed spec), implicit assumptions that clash, numeric/capacity contradictions (e.g., "handles 1M users" but "single SQLite database").

**Agent 3 — Ambiguity & Assumption Gaps** (optional but recommended)
Hunt for statements that appear consistent but hide contradictions behind vague language: terms used with multiple meanings, undefined behavior at boundaries, requirements that could be interpreted in conflicting ways depending on context.

Each agent must return findings in this format:
```
## [Agent Name] Findings

### Contradiction 1: [Short title]
- **Statement A:** [exact quote or paraphrase]
- **Statement B:** [exact quote or paraphrase]
- **Why these conflict:** [1-2 sentences]
- **Severity:** Critical / Moderate / Minor

### Contradiction 2: ...
(or "No contradictions found in this category.")
```

### Step 3: Synthesize & Present

After all agents return:
1. Deduplicate findings (multiple agents may catch the same issue)
2. Rank by severity (Critical first)
3. Present consolidated report to user via **AskUserQuestion**, asking them to confirm, clarify, or resolve each contradiction
4. Continue the conversation until all contradictions are resolved or acknowledged

### Step 4: Write Report

Once the user has addressed all findings, write a clean summary to a file using **Write**. Include:
- Original contradictions found
- User's resolutions
- Any remaining open items

<topic>$ARGUMENTS</topic>
