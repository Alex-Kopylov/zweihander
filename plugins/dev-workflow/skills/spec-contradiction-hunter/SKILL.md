---
argument-hint: [topic or paste the information to analyze]
name: spec-contradiction-hunter
description: This skill should be used when the user wants to "find contradictions", "check consistency", "validate my spec", "cross-check requirements", "spot inconsistencies", or has provided a body of information (spec, requirements, design doc) that needs consistency validation. Spawns parallel agents to hunt obvious and deeper contradictions.
allowed-tools: AskUserQuestion, Write, Read, Agent
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Spec Contradiction Hunter

Analyze user-provided specs, requirements, and design notes for internal contradictions, inconsistencies, and logical conflicts by dispatching parallel agents, each with a different analytical lens.

## Harness Adaptation

This skill uses Claude Code wording as the shared baseline. Identify the active assistant harness before translating tool names, agent dispatch, file writing, or user-question behavior. When harness-specific adaptation is needed, load exactly one matching metadata-linked harness reference for the active harness and skip all non-matching harness files.

## Process

### Step 1: Gather Information

If the user has not yet provided material to analyze, use **AskUserQuestion** to request it (spec, requirements, design decisions, constraints, etc.). Follow up until there is a substantial body of claims.

### Step 2: Dispatch Parallel Contradiction Hunters

Launch all applicable agents with the Agent tool in a **single message**. Pass the full collected information in each agent's `prompt`.

**Default agents:**
1. `surface-contradiction-hunter` — direct, obvious conflicts (required)
2. `structural-contradiction-hunter` — deeper logical/architectural incompatibilities (required)
3. `ambiguity-contradiction-hunter` — hidden contradictions behind vague language (include for any non-trivial input)

**Domain-specific agents (0..N):**

Review the collected material for domains where specialized knowledge would reveal contradictions the default agents may miss. For each clearly warranted domain, spawn an additional `general-purpose` agent with `model: "opus"` and a tailored prompt. Avoid speculative spawning.

### Step 3: Synthesize & Present

After all agents return:
1. Deduplicate findings (multiple agents may catch the same issue)
2. Rank by severity (Critical first)
3. Present consolidated report to user via **AskUserQuestion**, asking to confirm, clarify, or resolve each contradiction
4. Continue the conversation until all contradictions are resolved or acknowledged

### Step 4: Write Report

Once the user has addressed all findings, use **Write** to save a summary covering original contradictions, user resolutions, and open items.

<topic>$ARGUMENTS</topic>
