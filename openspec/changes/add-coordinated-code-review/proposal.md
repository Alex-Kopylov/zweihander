## Why

The marketplace already contains skills, agents, references, and examples for assessing completed work. A general reviewer should coordinate that existing expertise across code, tests, specifications, and agent-related Markdown without copying the expertise or modifying the reviewed material.

## What Changes

- Add a small general review coordinator, with a separate scope assessor, Markdown checkboxes, optional item-by-item interviewing, bounded discovery, and reviewer assignments. The skill's final name and plugin placement remain open.
- Map review items directly to existing marketplace skills, agents, and references. Do not create duplicate domain rubrics inside the coordinator.
- Add reusable `/to-agent-skill` delegation with an explicit parent/child orchestration hierarchy: inherited scope, read-only restrictions, state-write locations, budget, and output contract.
- Keep the supplied review-result schema in one file and hyperlink it from review-agent instructions. Prefer native schema enforcement; a bounded post-step can normalize existing skill output and validate it.
- Persist the live review plan and execution state to user-editable files. The reviewer can write only its own designated state. Research native harness isolation and workflow support before choosing an execution mechanism.

## Capabilities

### New Capabilities

- `coordinated-code-review`: General review selection, persistent planning, bounded discovery and assignments, coverage tracking, and aggregation. This existing capability ID is provisional and does not limit the feature to code.
- `skill-agent-delegation`: Reusable invocation of existing skills through agents with inherited orchestration constraints and a caller-supplied result contract.
- `composable-review-guidance`: Direct reuse of existing marketplace guidance without duplicated criteria or unintended implementation actions.

### Modified Capabilities

None. This checkout has no existing main capability specs to amend.

## Impact

Implementation will introduce a review coordinator and `to-agent-skill`, their orchestration references, and metadata for the chosen plugins. It will reuse `tests-manager`, `test-unit-reviewer`, `md-bloat-hunter`, and `agents-md-improver` through their existing entrypoints and resources. This change no longer prescribes new domain profiles or wholesale refactoring of those skills.

The requested `Follow conventions:` hyperlink already exists in `plugins/python-dev-workflow/agents/test-unit-reviewer.md`. The supplied schema is stored in [contracts/review-result.schema.json](contracts/review-result.schema.json).

**Planning is blocked for implementation.** The user will later choose the persistent plan's format, possibly a single executable orchestrator file. Native harness integration, effective isolation, and schema enforcement also remain unresolved design questions. These artifacts record the constraints and research; their existence does not mean implementation is ready.
