## 1. Resolve design blockers

- [ ] 1.1 **BLOCKED — user decision B1:** Define the persistent review-plan file's format, name, and location, including whether it also serves as a native executable orchestrator file.
- [ ] 1.2 **OPEN — research B2:** Record primary-source findings for Codex and Claude native orchestration, target-read-only/state-writable controls, and schema binding; distinguish current-tool limitations from other supported surfaces.
- [ ] 1.3 **BLOCKED by B1/B2:** Select the simplest verified native execution mechanism, or explicitly record the limitation without building a custom workflow engine or sandbox.
- [ ] 1.4 Settle the general-review skill name, plugin placement, scope-interview preference, model roles, and execution limits.

## 2. Wrap existing functionality

- [ ] 2.1 After the blockers are resolved, create the small `to-agent-skill` entrypoint and delegation contract with parent/child hierarchy, inherited scope, state-write paths, budget, and schema link.
- [ ] 2.2 Bind the contract to the selected native harness surfaces and ensure every nested orchestrator receives the same or narrower constraints.
- [ ] 2.3 Invoke existing skills, agents, and references directly; report incompatible source workflows and assess any narrow source-owned fix separately.

## 3. Coordinate general review and persistent state

- [ ] 3.1 Create the general review coordinator and a hyperlink-based mapping to existing marketplace capabilities; add no duplicate domain criteria.
- [ ] 3.2 Implement the user-selected on-disk plan format and active updates for scope, decisions, assignments, limits, progress, output paths, and gaps; preserve manual edits.
- [ ] 3.3 Define separate scope assessment, visible Markdown checkboxes, and the selected interview behavior; persist decisions before dispatch.
- [ ] 3.4 Define budgeted discovery, dedicated reviewers per item, explicitly optional batching, cross-file ownership, and result reconciliation from the current disk state.

## 4. Bind and validate review outputs

- [ ] 4.1 Place the canonical supplied schema in the selected review skill and hyperlink it from review-agent and subordinate-orchestrator instructions; do not duplicate schema bodies.
- [ ] 4.2 Use native structured output where verified; otherwise add only the agreed bounded normalization/validation post-step, preserving findings and reporting failure without invented fields.
- [ ] 4.3 Track failed, cancelled, unavailable, stale, and partial work in persistent state separately from the issue payload; verify and deduplicate findings.

## 5. Evaluate and package

- [ ] 5.1 Verify target immutability and allowed state writes using the selected harness, including a wrapped workflow that normally edits or publishes and a nested delegation attempt.
- [ ] 5.2 Verify manual plan edits, resume from disk, a non-code Markdown review, normalization from an existing skill's report, and a failed worker alongside an empty successful result.
- [ ] 5.3 Update README and both runtime manifests for only the plugins actually changed; run relevant validators, JSON checks, `git diff --check`, and strict OpenSpec validation.
