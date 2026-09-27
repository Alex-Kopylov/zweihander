# Pattern Catalog

Use this product- and domain-neutral catalog after framing the problem and decomposing it into stages. Do not treat every pattern as mandatory.

Source abstraction: Huang and Zhou, "A Two-Dimensional Framework for AI Agent Design Patterns: Cognitive Function x Execution Topology" (arXiv:2605.13850). This catalog preserves the reusable abstractions and omits vendor examples, case-study domains, exact matrix counts, benchmark numbers, token budgets, and example costs.

## Axes

### Cognitive Function

- Perception: decide what information enters working context.
- Memory: store, retrieve, update, or summarize knowledge.
- Reasoning: deliberate, classify, diagnose, plan, or decide.
- Action: call tools, invoke APIs, or change external state.
- Reflection: critique, verify, repair, or improve outputs.
- Collaboration: coordinate multiple agents, workers, roles, or reviewers.
- Governance: bound, observe, approve, contain, or control the system.

### Execution Topology

- Chain: linear sequence where each step feeds the next.
- Route: classify or gate early, then dispatch to a specialized path.
- Parallel: fan out independent work, then aggregate.
- Orchestrate: central coordinator delegates dynamic work and synthesizes results.
- Loop: repeat observe-adjust cycles until an exit condition is met.
- Hierarchy: nested delegation, containment, or policy layers.

## Perception Patterns

### Semantic Compact

- Topology: Chain.
- Use when raw context must be compressed before reasoning.
- Watch for loss of exact evidence, hidden assumptions, or summaries that remove minority signals.

### Context Triage

- Topology: Route.
- Use when many information sources compete for limited working context.
- Watch for over-filtering that drops critical context or under-filtering that dilutes attention.

### Multi-Modal Fusion

- Topology: Parallel.
- Use when independent input forms or evidence channels must be interpreted together.
- Watch for aggregation that hides conflicts between sources.

### Progressive Disclosure

- Topology: Orchestrate.
- Use when the system should load more context only after the task reveals a need.
- Watch for excessive back-and-forth or hidden latency from repeated context requests.

## Memory Patterns

### RAG Pipeline

- Topology: Chain.
- Use when the system needs external, changing, private, or larger-than-context knowledge.
- Watch for stale retrieval, weak ranking, and answers unsupported by retrieved evidence.

### Hierarchical Retrieval

- Topology: Route.
- Use when knowledge is split across specialized stores, abstraction levels, or access scopes.
- Watch for early misclassification that sends the query to the wrong memory path.

### Progress Tracking

- Topology: Orchestrate.
- Use when a coordinator must maintain task state across subtasks, tools, or workers.
- Watch for stale state, duplicate work, and unclear ownership of the current truth.

### Failure Journal

- Topology: Loop.
- Use when recurring errors should be recorded, summarized, and fed into future decisions.
- Watch for overfitting to old failures or preserving noisy postmortems as rules.

## Reasoning Patterns

### Structured Reasoning Chain

- Topology: Chain.
- Use when the answer depends on ordered analysis before conclusion.
- Watch for unsupported intermediate claims, unnecessary verbosity, or exposing private reasoning when a concise rationale is enough.

### Complexity Routing

- Topology: Route.
- Use when request difficulty varies widely and should change reasoning depth, model strength, or review effort.
- Watch for classifier errors that under-serve hard requests or over-spend on simple ones.

### Parallel Exploration

- Topology: Parallel.
- Use when multiple hypotheses, plans, or solution paths can be explored independently.
- Watch for expensive fan-out and weak aggregation that blends incompatible answers.

### Iterative Hypothesis Testing

- Topology: Loop.
- Use when the system must propose, probe, observe, and revise based on environmental feedback.
- Watch for missing exit conditions, speculative probing, or loops that continue after enough evidence exists.

## Action Patterns

### Prompt Chaining

- Topology: Chain.
- Use when a task is a stable sequence of transformations or tool calls.
- Watch for brittle dependencies where one weak early output corrupts every later step.

### Tool Dispatch

- Topology: Route.
- Use when a classifier can choose the correct tool, API, command, or handler.
- Watch for ambiguous tool boundaries and missing fallback paths.

### Plan-And-Execute

- Topology: Orchestrate.
- Use when dynamic subtasks, dependency management, or tool sequencing require a planner and executors.
- Watch for over-decomposition, under-specified subtasks, and plans that are not revised after execution feedback.

### Guardrail Sandwich

- Topology: Hierarchy.
- Use when actions need checks before and after execution, with policy layers around the tool call.
- Watch for superficial guardrails, duplicated policy logic, and post-checks that cannot repair damage.

## Reflection Patterns

### Generator-Critic

- Topology: Chain.
- Use when a first draft should be critiqued and revised before delivery.
- Watch for weak self-critique; prefer deterministic or independent feedback when available.

### Skill Package

- Topology: Route.
- Use when different output types need different reusable rubrics, evaluators, or correction procedures.
- Watch for routing to the wrong rubric or turning every small task into a heavy review workflow.

### Self-Heal Loop

- Topology: Loop.
- Use when an external verifier can fail the output, trigger diagnosis, and drive repair until the check passes or the attempt budget ends.
- Watch for flaky verifiers, repeated patches without new evidence, and missing stop conditions.

### Experience Replay

- Topology: Hierarchy.
- Use when the system should learn from prior attempts at task, session, project, or organization scope.
- Watch for replaying stale lessons into unrelated contexts.

## Collaboration Patterns

### Handoff Chain

- Topology: Chain.
- Use when roles should work in a fixed sequence and each role benefits from the previous role's output.
- Watch for context loss at handoff boundaries and late discovery that an earlier role must redo work.

### Fan-Out/Gather

- Topology: Parallel.
- Use when independent subtasks can be assigned to workers and aggregated afterward.
- Watch for false independence, inconsistent worker assumptions, and weak synthesis.

### Adversarial Review

- Topology: Loop.
- Use when a challenger should search for flaws, force revision, and repeat until objections are resolved or explicitly accepted.
- Watch for debate without evidence, endless disagreement, or reviewers optimizing for criticism rather than truth.

### Hierarchical Delegation

- Topology: Hierarchy.
- Use when work needs nested roles, specialization, or layered review.
- Watch for management overhead, hidden context loss, and vague delegation contracts.

## Governance Patterns

### Approval Gate

- Topology: Route.
- Use when actions should be auto-allowed, blocked, or sent to a human based on risk.
- Watch for approval fatigue, over-blocking safe actions, or under-classifying dangerous actions.

### Progressive Commit

- Topology: Parallel.
- Use when independent changes or decisions can be verified and committed in small units.
- Watch for partial commits that create inconsistent system state.

### Observability Harness

- Topology: Orchestrate.
- Use when tracing, logging, evaluation, and alerting must be coordinated across workflow stages.
- Watch for logs that cannot explain decisions or metrics disconnected from user-impacting failures.

### Blast Radius Control

- Topology: Hierarchy.
- Use when layered containment should limit the maximum damage from mistakes or tool interactions.
- Watch for sandboxes that block legitimate work or permissions that bypass the real risk boundary.

## Selection Pressures

- Strong time pressure favors Chain or Route and argues against deep orchestration unless risk requires it.
- High volume favors Route, Parallel, or Hierarchy if work can be split safely.
- Dynamic dependencies favor Orchestrate or Loop.
- External actions require Governance patterns before autonomy increases.
- Irreversible or high-impact actions require stronger containment and approval.
- Asymmetric failure costs should bias reflection and routing toward the safer error.
- Objective verification favors Self-Heal Loop; subjective quality review favors Generator-Critic.
- Variable request difficulty favors Complexity Routing before expensive reasoning.
- Large or unstable knowledge needs favor Memory patterns with evidence checks.
- Multi-agent collaboration is justified by separability, specialization, or independent review, not by novelty.

## Common Pairings

- Context Triage + RAG Pipeline: choose relevant context, then retrieve evidence.
- Complexity Routing + Structured Reasoning Chain: reserve deeper reasoning for harder requests.
- Tool Dispatch + Approval Gate: select the tool path, then gate risky actions.
- Plan-And-Execute + Progress Tracking: coordinate dynamic tool work and keep state current.
- Generator-Critic + Self-Heal Loop: combine subjective critique with objective repair when both are needed.
- Fan-Out/Gather + Hierarchical Delegation: process large separable work while preserving role structure.
- Observability Harness + Blast Radius Control: monitor autonomous behavior inside bounded execution.
