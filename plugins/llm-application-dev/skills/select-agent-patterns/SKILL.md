---
name: select-agent-patterns
description: Use when choosing LLM agent or LLM workflow design patterns for a presented problem, decomposing an LLM-based system into stages, comparing candidate agent architectures, selecting execution topologies such as chain, route, parallel, orchestrate, loop, or hierarchy, or producing a final recommendation for which patterns fit each stage. Also use when the user asks for agent architecture trade-offs, pattern selection, workflow decomposition, multi-agent design, reflection or governance patterns, or a framework-neutral way to decide how an LLM system should be structured.
---

# Select Agent Patterns

Select LLM application patterns by separating what each stage must do from how that stage should be wired. Treat patterns as composable structural templates, not as a fixed architecture catalog.

Use only the paper's cognitive-function and execution-topology abstractions; do not preserve its product references, case-study domains, benchmark numbers, matrix dimensions, or literal example quantities.

## Core Rule

Pick patterns for the user's specific problem, not for the paper's examples. One LLM system can use different patterns at different stages.

Before recommending patterns, strip away:

- Vendor, product, framework, and case-study names unless the user's problem requires them.
- Literal matrix sizes, benchmark numbers, token counts, and example costs.
- Domain-specific policy choices from examples.

Keep reusable decision variables:

- Time pressure and latency tolerance.
- Volume, concurrency, and stream versus batch shape.
- Action authority, reversibility, and blast radius.
- Failure cost asymmetry.
- Context size, source quality, and memory needs.
- Need for evidence, verification, observability, auditability, or human approval.

## Workflow

Use `work-session-tools:task-management` when the selection task needs tracked stages, parallel reviewer passes, or explicit synthesis status.

### 1. Understand The Problem

Build a compact problem frame:

- Goal: what the user needs the LLM system to accomplish.
- Inputs: messages, files, retrieved data, tools, events, or external systems.
- Outputs: answer, artifact, tool action, decision, workflow state, or handoff.
- Constraints: latency, cost, reliability, privacy, safety, human review, and reversibility.
- Failure model: most important mistakes and their relative severity.

Ask a brief clarification only when a missing constraint could change the pattern choice materially. Otherwise state assumptions and proceed.

### 2. Decompose Into Stages

Split the system by cognitive purpose, not by implementation component names. Use the catalog's cognitive-function axis as the stage taxonomy: Perception, Memory, Reasoning, Action, Reflection, Collaboration, and Governance; treat Governance as including observation, approval, containment, and rate limiting.

For each stage, record the stage input, output, dependency on prior stages, authority level, and verifier.

### 3. Generate Candidate Patterns

Read `references/pattern-catalog.md`. For each stage, shortlist candidate patterns whose cognitive function and topology fit the problem constraints.

Use `references/pattern-catalog.md` as the source of topology definitions and prefer the simplest topology that satisfies the stage constraints: Chain, Route, Parallel, Orchestrate, Loop, or Hierarchy.

Always consider governance when the system can call tools, spend money, mutate state, expose data, or create user-visible decisions.

### 4. Review Each Pattern Independently

Review each candidate pattern independently. When subagents are available, run `agents/pattern-fit-reviewer.md` once per candidate with only the problem frame, stage, and candidate pattern. Otherwise, write separate passes so one candidate's conclusion does not contaminate another's review.

Each review should follow the output contract in `agents/pattern-fit-reviewer.md`, whether run as a subagent or emulated as an independent written pass.

### 5. Synthesize The Architecture

Compare reviewer outputs stage by stage. Select the pattern set that best satisfies the constraints with the least unnecessary coordination.

Use these synthesis rules:

- A workflow may combine multiple patterns across stages.
- A stage may need no agent pattern if deterministic code, a direct model call, or a simple schema is enough.
- Prefer deterministic validators over self-critique when objective checks exist.
- Add reflection when first-pass output errors are likely or expensive.
- Add routing before expensive reasoning when request difficulty varies.
- Add collaboration only when work is genuinely separable or needs distinct expertise.
- Add containment before autonomy, not after an incident.

## Final Report

Return a concise architecture report:

1. Problem frame and assumptions.
2. Stage decomposition.
3. Recommended pattern per stage, with cognitive function and topology.
4. Why each selected pattern fits.
5. Rejected alternatives and why they lost.
6. Cross-stage workflow sketch.
7. Governance, verification, and observability requirements.
8. Open questions that would change the recommendation.

Do not dump the full catalog; include only patterns considered or selected.
