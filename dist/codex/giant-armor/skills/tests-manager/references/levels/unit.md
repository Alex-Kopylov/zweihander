# Unit Level

## Owns

Local decisions that can be isolated from system wiring: validation, guard
clauses, exception paths, edge values, and service or handler branching.

Cover a branch, guard, exception path, or edge value here only when no test at
any layer already owns it. An integration or E2E test that proves a branch is
its owner; do not repeat it as a unit case.

For an endpoint handler, the unit layer owns input validation, permission
branches, and error mapping that the higher layers do not already prove.

## Rules

- Place tests under the mirrored `tests/unit/` path; see
  [placement](../rules/conventions.md#placement).
- Replace only I/O boundaries; see [mocking boundaries](../rules/mocking.md#boundaries).
- Verify output and observable state first. Assert a call only when the
  interaction is the contract.
- Stay at the assigned level. Report a missing integration or E2E proof as a
  gap instead of widening the unit test into one.
