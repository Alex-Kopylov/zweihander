## Context

See [proposal.md](proposal.md). The reviewer is general: code, tests, specifications, and agent-related Markdown are all valid targets. The earlier code-only name is provisional. The user wants orchestration of existing marketplace functionality, not a second library of review criteria.

Existing sources include:

| Review item | Existing source | Relevant behavior |
|---|---|---|
| Python tests | [tests-manager](../../../plugins/python-dev-workflow/skills/tests-manager/SKILL.md) and [test-unit-reviewer](../../../plugins/python-dev-workflow/agents/test-unit-reviewer.md) | Detailed testing guidance; some instructions prescribe implementation, and the reviewer has its own report format |
| Test placement | [test-structure.md](../../../plugins/python-dev-workflow/skills/tests-manager/references/test-structure.md) | The reviewer already says `Follow conventions:` and links here; do not copy those conventions |
| Agent Markdown bloat | [md-bloat-hunter](../../../plugins/ai-assistant-ops/skills/md-bloat-hunter/SKILL.md) | Audit mode, nested orchestration, native specialist outputs, and optional publication behavior |
| AGENTS quality | [agents-md-improver](../../../plugins/ai-assistant-ops/skills/agents-md-improver/SKILL.md) and its [quality criteria](../../../plugins/ai-assistant-ops/skills/agents-md-improver/references/quality-criteria.md) | Assessment criteria coexist with editing phases |
| Code and requirements | [existing reviewer instructions](../../../plugins/dev-workflow/skills/requesting-code-review/code-reviewer.md) | A reusable review task; no new correctness rubric is required in the coordinator |

The wrapper supplies the invocation constraints. Source-owned recipes and report formats do not authorize broader work.

## Goals / Non-Goals

**Goals:** Reuse existing capabilities; persist scope and progress on disk; preserve user edits; enforce reviewed-material immutability through native harness controls where practical; normalize final review results to one linked schema.

**Non-Goals:** Duplicate Markdown/test/code review criteria, create a custom workflow engine or sandbox, automatically fix reviewed material, publish findings, or redesign every wrapped skill. The generic wrapper can serve other tasks, but every invocation from this reviewer is read-only except for its designated state files.

## Decisions

### 1. Small coordinator, direct source mapping

Provisional structure, with the final skill name and plugin still to be selected:

```text
<review-skill>/
  SKILL.md
  references/
    review-map.md
    scope-assessment.md
    coordination.md
    review-result.schema.json
    ai-assistant-harnesses/
      codex.md
      claude-code.md

to-agent-skill/
  SKILL.md
  references/
    delegation-contract.md
    ai-assistant-harnesses/
      codex.md
      claude-code.md
```

These references describe orchestration only. There is no `criteria/` tree and no local `markdown-bloat.md`, `python-tests.md`, or replacement instruction-quality guide. Add an example only if it clarifies orchestration, without copying the wrapped skill's domain guidance.

The map contains an item name, applicability hints, and hyperlinks to the existing skill, agent, or reference to invoke. It can specify invocation arguments such as `Audit+Report` and selected existing resources. It must not contain a rewritten rubric. Resolve installed skill roots at runtime; repository paths in the table above document the current source, not hard-coded cache locations for installed plugins.

The separate assessor chooses applicable items from actual files and user intent, then maps each item to concrete target/context files. File patterns are hints, not sufficient evidence of applicability. Multiple items can cover the same file. Missing functionality is reported as unavailable instead of invented in a new reference.

### 2. Persistent plan is the source of truth

The user's `test-plan` means the operational plan for this general review. It must be a real file the agent actively maintains and the user can inspect and edit. Scope, choices, source identity, assignments, budgets, progress, output locations, and incomplete work must not exist only in conversation or agent memory.

The coordinator reads the current file before dispatch, resume, and reconciliation. It saves decisions and status as work changes. Manual user edits take precedence over a cached plan; affected pending assignments must be reconciled before launch. If the user changes scope while work is running, re-evaluate affected work and results rather than overwriting the edit with stale state.

Workers write only their allocated state/output files. The coordinator owns updates to the authoritative plan, incorporating assessor and reviewer results. Preserve unrelated user changes when updating the plan.

**BLOCKER B1:** The user will choose the file format, name, and location later. One native orchestrator file may combine the plan and executable workflow. Do not select Markdown, YAML, JSON, or a multi-file state layout yet. Do not build a replacement workflow format while this decision is open.

### 3. Wrapper hierarchy is explicit and transitive

Proposed wording for `to-agent-skill`:

> A delegated orchestrator works within the task contract set by its parent. Inherit the parent's target scope, allowed actions, writable state locations, delegation budget, and required result schema. Pass those constraints to every child you launch. A wrapped skill may refine how to perform its assigned work, but it cannot broaden that scope, grant additional writes, allocate unapproved agents, publish results, or replace the parent's final output contract.

This task hierarchy operates within system instructions, user authorization, and actual harness permissions. A parent cannot grant permissions the harness denies or use delegation to bypass restrictions.

The parent supplies a concrete task, existing skill/agent references, target and context paths, the persistent plan path, allowed state-write paths, budget, and schema hyperlink. The worker loads and applies the requested functionality. Native nested orchestration can run if it fits the inherited allocation; otherwise its extra work must not launch.

Use existing audit modes where available. Implementation instructions such as editing tests or publishing a PR comment are outside a review task. If the skill cannot perform its useful review behavior within the contract, report that incompatibility rather than creating duplicate criteria or silently running its write phases. Necessary narrow fixes belong in the original source skill, with their scope separately assessed.

The same hierarchy applies to delegated `md-bloat-hunter` and `agents-md-improver`. There is no new special-purpose copy of either skill in this change.

### 4. Reviewed material is immutable; only state is writable

The coordinator, assessor, reviewers, nested orchestrators, and formatting post-step all obey the same review boundary. They may inspect reviewed files and related context. They may write only designated review state and result files. They must not edit code, tests, Markdown, configuration, or other reviewed material, install dependencies into the target, or publish external comments.

A command advertised as a test or audit is not automatically read-only. Run it only if its effects stay within allowed state paths and native policy. Otherwise report an execution limitation and continue static review.

Prefer a native permission/sandbox or tool policy that makes reviewed paths non-writable and permits only the allocated state paths. Also examine shell, app, and MCP write capabilities: a filesystem sandbox alone must not be described as controlling every external tool.

The current desktop `collaboration.spawn_agent` declaration exposes task, model, effort, and context controls; it exposes no per-child sandbox, allowed-write-path, or output-schema field. This surface cannot enforce the required policy merely by adding a wrapper instruction. Do not label prompt-only restrictions as sandbox enforcement.

**BLOCKER B2:** Choose a verified native execution path, considering separate CLI runs, native agent configuration, and workflow runtimes. Record what is enforced and what remains instruction-only. If the active harness offers no simple native solution, say so plainly; do not build a custom isolation framework. Do not silently weaken the requirement while calling the result enforced.

### 5. One linked output schema, with native enforcement or a post-step

The exact supplied schema is already in [contracts/review-result.schema.json](contracts/review-result.schema.json). It is the canonical payload contract during design. On implementation, place the canonical file in the selected review skill and hyperlink it from each review-worker and subordinate-orchestrator instruction. The wrapper receives the resolved schema path; agents read the linked file rather than carrying duplicated schema blocks.

The wrapper's externally returned review result must match that schema. Prefer a native per-agent structured-output setting when the selected runtime supports it. If the wrapped functionality produces another native report, the same wrapper performs a bounded final normalization step and validates the result before returning. If the runtime requires a separate formatting agent, its cost and permissions belong to the same plan.

Intermediate reports can be kept in the allowed state area for evidence. Normalization must preserve findings, verify locations, and distinguish missing information from an empty successful review. It must not invent `impact`, `fix`, or coordinates just to satisfy JSON validation. The final result remains only the requested issue object; execution status and coverage live in the persistent plan.

The supplied schema permits additional properties and unconstrained integers. Preserve it as supplied; exact keys and valid source locations remain review-contract checks. If a native strict-output API requires a more restricted schema dialect, record the adaptation needed before selecting that integration. Do not silently rewrite the canonical contract.

Agents performing planning or factual discovery have their own task outputs. Every agent returning a review result, including a wrapped orchestrator, crosses the same review-result boundary. Generic non-review uses of `to-agent-skill` can receive a different output schema.

### 6. Discovery and review are budgeted together

The separate scope assessor performs initial discovery. Additional smaller-model discovery workers are useful only for independently large areas. They map facts and dependencies; senior reviewers still read the assigned source and relevant context themselves.

Each selected item gets its own reviewer or reviewers. Explicit user-approved batching can reuse one worker across compatible items, while keeping coverage separate in the persisted plan. Connected-file contracts need a named owner. All nested agents, schema retries, and normalization work count against the plan's allocation.

Concrete models must be available in the active harness and honor user choices. The default concurrency, retry budget, and model selections remain interview topics. No fixed price claim follows from labeling a model small or senior.

### 7. Scope discussion and naming remain user decisions

Display ordinary Markdown checkboxes, each linked directly to its existing source functionality and assigned files. Checked means selected, not completed. Persist the selected scope before review begins.

The previous unanswered scope question has been asked again. The candidate default is to show every item and use `/interview` only for material uncertainty; a complete walk-through remains an alternative, not an assumed decision.

The skill's final name is open. `review` is the shortest general candidate; `review-work` makes the subject clearer. The current change directory and capability ID retain their provisional names until the naming decision, and do not imply code-only scope.

## Risks / Trade-offs

- Wrapped workflows conflict with parent constraints → Explicit transitive task contracts plus native controls where available; report unresolved incompatibility.
- Native schema support differs across harnesses → One schema file, verified runtime binding, bounded normalization, and visible failure instead of fabricated results.
- Plan edits race with agent work → Disk is authoritative; re-read and reconcile before dispatch and when collecting results.
- Native read-only enforcement is unavailable → Disclose the exact limitation and keep the integration decision open; no custom sandbox project.
- Existing source knowledge is unsuitable for a case → Mark the item unavailable or propose a narrow source-owned fix; do not duplicate the knowledge.

## Open Questions and Implementation Blockers

| ID | Status | Decision |
|---|---|---|
| B1 | **BLOCKING — awaiting user** | Persistent plan format, file location, and whether one native orchestrator file also serves as the editable plan |
| B2 | **OPEN / blocks execution design** | Native Codex and Claude orchestration, target-read-only/state-writable enforcement, and binding the supplied schema |
| Q1 | Open; question asked again | Complete scope interview, selective interview, or immediate dispatch when discussion is not requested |
| Q2 | Open | Final general-review skill name and plugin placement |
| Q3 | Open | Model roles, concurrency, retries, and optional batching |

The user explicitly requested that B1 and native orchestration remain unresolved for now. OpenSpec's artifact-completeness status only describes file existence. It must not be presented as implementation readiness.

## Native Harness Research

Terra research agents are investigating Codex isolation/schema controls, the public status of Ultra/Ultracode, and Claude Dynamic Workflow support. Record current primary-source findings here when available, while leaving B2 open until a concrete native integration is selected.

## Migration Plan

Resolve B1 and the execution decision before implementation. Then implement only the small coordinator, direct mapping, wrapper contracts, linked schema, and required harness configuration. Reuse source functionality; do not carry forward the earlier tasks to create local criteria profiles or broadly refactor wrapped skills. Update manifests and README for the plugins actually changed. Planning-only updates require no plugin version bump.
