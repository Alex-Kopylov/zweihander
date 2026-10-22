## Purpose

Coordinate read-only review of completed work, including code, tests, specifications, and agent-related Markdown, through existing marketplace capabilities and persistent user-editable state.

## ADDED Requirements

### Requirement: Review scope is general and visibly selected

The coordinator SHALL use a separate scope assessor to identify applicable review items, target/context files, existing source functionality, and reasons from the user's request and actual material. It MUST support non-code targets. It SHALL show ordinary Markdown checkboxes linking each item to its existing skill, agent, or reference. Checked boxes SHALL mean selected, not completed. User preferences and unresolved scope choices SHALL be handled through the selected interview behavior and saved to disk.

#### Scenario: Review contains only agent-related Markdown

- **WHEN** the user requests review of SKILL or AGENTS files without source-code changes
- **THEN** the assessor proposes applicable existing Markdown and instruction-review functionality
- **AND** it does not require a code diff or substitute a new local rubric

#### Scenario: User requests a complete interview

- **WHEN** the user asks to discuss every proposed item
- **THEN** each item receives an explicit decision through the interview
- **AND** those decisions are persisted before dependent review work starts

### Requirement: Live review plan is persisted and user-editable

The review plan SHALL be a file the agent actively maintains and the user can inspect and edit. It SHALL persist scope, user decisions, source identity, assignments, execution limits, progress, result locations, and coverage gaps. The current file MUST be authoritative over cached conversation or agent memory. The coordinator MUST re-read it before dispatch and resume and reconcile edits when collecting results. Implementation of the file representation MUST await the user's format decision.

#### Scenario: User edits the plan before dispatch

- **WHEN** the user removes an item or changes its files in the saved plan
- **THEN** the coordinator uses that edited scope for subsequent assignments
- **AND** it does not overwrite the change with a cached version

#### Scenario: A review resumes after losing conversational context

- **WHEN** a review resumes with only its saved plan and result files
- **THEN** the coordinator can identify selected work, completed work, and unresolved work from those files
- **AND** it does not depend on hidden in-memory assignments

#### Scenario: User has not chosen a file format

- **WHEN** the persistent plan representation remains undecided
- **THEN** implementation remains blocked at that decision
- **AND** the coordinator design does not silently choose an ephemeral or custom executable format

### Requirement: Review changes only its designated state

The coordinator and all agents it launches SHALL treat reviewed code, tests, Markdown, configuration, and other target material as read-only. They SHALL write only their allocated review state and result files. They MUST NOT install target dependencies, apply suggested fixes, or publish external comments. Native harness controls SHALL enforce these boundaries where supported. The system MUST disclose exactly which restrictions are enforced and MUST NOT represent a prompt instruction as a native restriction.

#### Scenario: Wrapped skill normally edits or publishes

- **WHEN** the selected source workflow contains editing or PR-comment phases
- **THEN** those phases remain outside the inherited review task
- **AND** only allocated state files can be written

#### Scenario: Current spawn tool lacks per-child isolation controls

- **WHEN** the active agent-spawn surface cannot set the required native policy
- **THEN** the coordinator reports the limitation and identifies any verified supported execution route
- **AND** it does not invent an unavailable argument, claim enforcement, or build a custom sandbox as a workaround

#### Scenario: Test command would modify reviewed material

- **WHEN** an optional test or audit command would write outside the allowed state area
- **THEN** the command is not run as part of the read-only review
- **AND** static review can continue with the execution limitation recorded

### Requirement: Reviewer assignments are bounded and accountable

Each selected item SHALL receive one or more dedicated reviewers by default. Compatible items SHALL share a worker only when the user explicitly chooses batching. The persisted plan SHALL account for discovery, nested agents, retries, normalization, and cross-file review ownership within its limits. Discovery SHALL provide factual navigation; reviewers MUST independently inspect their assigned material and necessary context. Missing source functionality MUST remain visible as unavailable coverage.

#### Scenario: Existing orchestrator requests additional workers

- **WHEN** a wrapped orchestrator would launch children beyond its assigned budget
- **THEN** that fan-out does not run
- **AND** the allocation mismatch is recorded for the parent coordinator

#### Scenario: Related files belong to different reviewer groups

- **WHEN** correctness depends on a contract across those groups
- **THEN** the plan assigns responsibility for checking that contract before claiming complete coverage

### Requirement: Review results use one linked schema

Every review-result producer SHALL reference the canonical [review-result schema](../../contracts/review-result.schema.json) through a hyperlink rather than duplicate its definition. Its final returned result MUST match that schema and the review contract. Native structured output SHALL be used where the selected integration supports it; otherwise an agreed bounded normalization and validation step SHALL enforce the final payload boundary. Planning and factual-discovery outputs SHALL remain distinct from review results.

The review contract SHALL require the requested key sets, non-empty finding text, and real source-relative locations with positive one-based line and column numbers. Columns SHALL count Unicode code points. A completed review without findings SHALL return an empty issue array. The system MUST NOT invent locations, consequences, or corrections to satisfy the schema.

#### Scenario: Existing skill returns a different report format

- **WHEN** a wrapped skill produces a useful native report with a different structure
- **THEN** the wrapper normalizes that report to the linked schema before returning
- **AND** missing required evidence becomes a visible incomplete result rather than fabricated content

#### Scenario: Native API requires a different schema dialect

- **WHEN** a native structured-output API cannot accept the supplied schema as written
- **THEN** the integration records the exact incompatibility before choosing a binding
- **AND** it does not silently alter the canonical file

### Requirement: Aggregation preserves evidence and incomplete coverage

The coordinator SHALL verify evidence and locations, deduplicate the same underlying defect, and resolve contradictory claims before accepting them. It SHALL persist execution status and coverage separately from the issue payload. Missing, failed, cancelled, unavailable, or stale work MUST remain visible. Changed targets MUST invalidate affected results or be explicitly reported as stale.

#### Scenario: One reviewer fails while another finds no issues

- **WHEN** one selected assignment fails and another returns an empty issue array
- **THEN** the saved plan and user-facing report identify the incomplete assignment
- **AND** the review is not represented as complete and clean

#### Scenario: User requests JSON-only output but required work fails

- **WHEN** the requested successful payload cannot be produced after the allocated attempts
- **THEN** execution fails explicitly through the available task-failure reporting path
- **AND** failure is not disguised as an empty successful review or a fabricated finding
