## Purpose

Invoke existing skills or agents within a delegated task while preserving parent orchestration constraints, native permissions, persistent state, and the caller's result contract.

## ADDED Requirements

### Requirement: Wrapper invokes existing functionality

`/to-agent-skill` SHALL accept a concrete task, existing skill or agent references, required context, the persistent plan path, allowed actions and state paths, delegation limits, and an optional schema-file link. It SHALL resolve and invoke that functionality in a separate agent through an available supported mechanism. It MUST NOT replace the source expertise with duplicated domain instructions.

#### Scenario: Reviewer wraps Markdown audit

- **WHEN** the caller selects `md-bloat-hunter` in its existing audit mode
- **THEN** the worker applies that existing functionality with the caller's constraints
- **AND** it does not substitute a newly authored Markdown-bloat rubric

### Requirement: Child orchestrators inherit the parent's task contract

A delegated orchestrator SHALL inherit its parent's target scope, allowed actions, writable state paths, delegation budget, and result contract. It MUST pass those constraints, or narrower ones, to every child. Wrapped skill instructions MUST NOT expand that delegated authority, publish results, or replace the required final output format. This task hierarchy MUST remain subject to system instructions, user authorization, and actual harness policy.

#### Scenario: Child skill requests editing or publication

- **WHEN** a wrapped skill's ordinary workflow includes changing targets or posting findings
- **THEN** the inherited read-only review contract excludes those actions
- **AND** any inability to perform useful work within that contract is returned to the parent

#### Scenario: Child orchestrator launches another orchestrator

- **WHEN** nested orchestration is supported and included in the parent's budget
- **THEN** the child receives the same or narrower task and state-write restrictions
- **AND** nesting does not reset permissions, budget, or output requirements

### Requirement: Native enforcement is distinguished from instructions

The wrapper SHALL prefer supported native permission, tool, sandbox, and structured-output controls. It MUST record their effective scope and limitations. When the active spawn surface lacks required controls, it SHALL report that limitation and keep the execution choice unresolved rather than emulate unavailable controls or implement a custom enforcement framework.

#### Scenario: Parent is unrestricted and spawn has no permission override

- **WHEN** the runtime cannot attach a restrictive policy to that child
- **THEN** the wrapper does not describe its read-only instruction as enforced isolation
- **AND** it identifies a separately verified native execution route if one exists

#### Scenario: Filesystem policy does not govern external tools

- **WHEN** app or MCP tools remain outside filesystem sandbox controls
- **THEN** the wrapper accounts for their write capabilities separately
- **AND** it does not claim that filesystem protection prevents external mutations

### Requirement: Final result honors the linked caller contract

The wrapper SHALL resolve and load the caller's schema-file hyperlink. Review invocations SHALL use the canonical [review-result schema](../../contracts/review-result.schema.json). Native schema enforcement SHALL be preferred; a bounded post-step SHALL normalize existing source reports when necessary. The returned result MUST be validated, and unsupported or invalid outputs MUST remain task failures. Intermediate source outputs SHALL be stored only in allocated state.

#### Scenario: Native workflow agent accepts a JSON Schema

- **WHEN** the selected harness offers a verified per-agent schema parameter
- **THEN** the wrapper binds the canonical contract through that supported mechanism
- **AND** it does not create a separate custom workflow runner

#### Scenario: Wrapped report lacks required location evidence

- **WHEN** normalization cannot recover a real file, line, or column from inspected material
- **THEN** the wrapper records the incomplete result
- **AND** it does not fabricate coordinates to pass validation

### Requirement: Generic wrapper remains usable outside review

Non-review invocations SHALL follow their own explicit task and result contract. The review-specific schema and immutable-target rule SHALL apply whenever the wrapper is called by the general reviewer. Missing skills, unsupported nesting, unavailable delegation, and failed execution MUST be reported without silent substitution.

#### Scenario: Wrapper delegates a non-review planning task

- **WHEN** the caller supplies a planning skill and a different result schema
- **THEN** the worker uses that caller's contract
- **AND** it is not forced into an issue array
