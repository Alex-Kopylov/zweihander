---
argument-hint: [topic or paste the information to analyze]
name: contradiction-hunter
description: This skill should be used when the user wants to "find contradictions", "check consistency", "validate my spec", "cross-check requirements", "spot inconsistencies", or has provided a body of information (spec, requirements, design doc) that needs consistency validation. Spawns parallel agents to hunt obvious and deeper contradictions.
allowed-tools: AskUserQuestion, Write, Read, Agent
---

# Contradiction Hunter

Analyze user-provided information for internal contradictions, inconsistencies, and logical conflicts by dispatching parallel agents, each with a different analytical lens.

## Process

### Step 1: Gather Information

If the user has not yet provided the information to analyze, use **AskUserQuestion** to ask for the material (spec, requirements, design decisions, constraints, etc.). Follow up until there is a substantial body of claims to analyze.

### Step 2: Dispatch Parallel Contradiction Hunters

Launch all applicable agents in a **single message** using the Agent tool. Pass the full collected information in each agent's `prompt` parameter.

**Default agents:**
1. `surface-contradiction-hunter` — direct, obvious conflicts (required)
2. `structural-contradiction-hunter` — deeper logical/architectural incompatibilities (required)
3. `ambiguity-contradiction-hunter` — hidden contradictions behind vague language (include for any non-trivial input)

**Domain-specific agents (0..N):**

Review the collected material for domain-specific aspects the default agents are not equipped to catch. For each identified domain, spawn an additional `general-purpose` agent with `model: "opus"` and a tailored prompt targeting that domain's contradiction patterns.

Spawn a domain-specific agent for any domain where specialized knowledge would reveal contradictions the default agents would miss. Avoid speculative spawning — only when the material clearly warrants it.

### Step 3: Synthesize & Present

After all agents return:
1. Deduplicate findings (multiple agents may catch the same issue)
2. Rank by severity (Critical first)
3. Present consolidated report to user via **AskUserQuestion**, asking to confirm, clarify, or resolve each contradiction
4. Continue the conversation until all contradictions are resolved or acknowledged

### Step 4: Write Report

Once the user has addressed all findings, write a clean summary to a file using **Write**. Include:
- Original contradictions found
- User's resolutions
- Any remaining open items

<topic>$ARGUMENTS</topic>
