# Review Step

One step: judge new or changed tests in one lane before they are accepted.

## Input

The lane's diff and the requirements or scenario catalog. Read the neighbouring
tests of the same production owners, and the owners themselves, from the
checkout. Nothing else: not the writer's plan, reasoning, or transcript.

## Conformance

For each new or changed test, check:

- the [value bar](../rules/test-value.md#value-bar) and every
  [junk pattern](../rules/test-value.md#junk-patterns);
- the [conventions](../rules/conventions.md);
- the [mocking rules](../rules/mocking.md) when the test uses doubles;
- that its level owns what it proves: [unit](../levels/unit.md),
  [integration](../levels/integration.md), or [E2E](../levels/e2e.md);
- that a neighbouring test does not already prove the same contract.

## Gaps against requirements

Every requirement, scenario, and corner case has proof at some level. A branch
needs a unit test only when no test at any layer owns it. A bug fix has one
regression test at the owner boundary. Record each missing proof in the
ledger's `gaps`, naming the requirement or scenario.

## Deletion bar

Low. The author is present and nothing is accepted yet, so a junk-pattern match
or an unanswered authoring-gate question is enough to mark a new test `D` or
`F` with a one-line reason. The audit evidence fields are not required.

## Output

A ledger in `review` mode: one entry per new or changed test, plus an entry for
a neighbouring test only when the diff makes it redundant. Marks follow
[ledger marks](../rules/test-value.md#ledger-marks).
