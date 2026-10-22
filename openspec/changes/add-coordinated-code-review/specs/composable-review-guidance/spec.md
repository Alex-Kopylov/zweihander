## Purpose

Reuse marketplace skills, agents, references, and examples directly for general review, with source-owned domain knowledge and caller-controlled execution.

## ADDED Requirements

### Requirement: Mapping links directly to existing knowledge

The review map SHALL connect an item and its applicability to existing skills, agents, or reference files through hyperlinks. The review coordinator MUST NOT duplicate their domain criteria in local profiles. Selected resources SHALL resolve relative to their owning installed skill. Examples SHALL be used as illustrations within their original context.

#### Scenario: Test placement conventions already have a reference

- **WHEN** test placement is part of the selected review
- **THEN** the reviewer follows the existing test-structure reference through a hyperlink
- **AND** it does not copy the placement rules or append an independently maintained exception

#### Scenario: Existing Markdown-bloat capability is selected

- **WHEN** the reviewer selects Markdown-bloat analysis
- **THEN** the map routes directly to the existing skill or its existing agents/resources
- **AND** the coordinator contains no duplicate Markdown-bloat guide

### Requirement: Wrapped workflows operate under the parent contract

Existing functionality SHALL run within the wrapper's inherited scope, read-only target boundary, state-write allocation, agent budget, and final result contract. Existing audit modes SHALL be used when applicable. Implementation or publication instructions in a source workflow MUST NOT become authorized actions merely because the source was loaded.

#### Scenario: Testing guidance prescribes RED and rewriting

- **WHEN** a review worker encounters implementation-only TDD instructions
- **THEN** it evaluates completed work within its review assignment
- **AND** it does not rewrite tests or source to manufacture RED

#### Scenario: Audit skill has a PR-comment follow-up

- **WHEN** that skill is invoked through a read-only review wrapper
- **THEN** the worker returns findings to its parent
- **AND** it does not publish them

### Requirement: Source report formats can be normalized without copying expertise

The wrapper SHALL allow existing functionality to produce an intermediate native report and SHALL normalize its final returned review result to the linked schema. It MUST preserve evidence and expose missing required information. Formatting adaptation MUST NOT introduce a second copy of the source's review criteria.

#### Scenario: Specialist returns Markdown findings

- **WHEN** the existing specialist reports findings in Markdown
- **THEN** the wrapper converts the supported findings into the canonical issue payload
- **AND** it verifies locations and records incomplete evidence instead of inventing it

### Requirement: Incompatible or missing sources remain visible

The coordinator SHALL report unavailable functionality and source workflows that cannot perform useful review within the inherited contract. It MUST NOT silently substitute new local guidance. Any necessary source-content fix SHALL be assessed in its owning skill rather than assumed as a broad prerequisite refactor.

#### Scenario: Skill cannot operate without unauthorized mutation

- **WHEN** its useful behavior cannot be restricted to review and designated state writes
- **THEN** the selected item is marked incompatible or incomplete
- **AND** the coordinator does not create a duplicate implementation of that skill
