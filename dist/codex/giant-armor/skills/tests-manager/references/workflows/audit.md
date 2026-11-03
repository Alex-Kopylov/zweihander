# Audit Step

One step: prune an area's existing tests, and the test-only production seams
they keep alive, without losing a contract. An audit always works in lanes,
whether the area has one lane or many. Optimize for confidence, not deletion
count: a few well-evidenced removals beat a large speculative list.

Never edit source or tests while pytest or mutmut is running in the checkout.

## Baseline

Record every in-scope test's result before any edit:

```bash
uv run pytest <scope> --junitxml=<run-dir>/baseline.xml
```

Keep the baseline failures in their own list. A retained test that fails on the
baseline is a product-bug lead, not a stale test.

## Ledger

Per lane, read-only. Read every assigned test in full, including `parametrize`
tables and fixtures. Read its production owners with their entry points,
callers, and history (`git log --follow`, `git log -L`), and how CI selects the
tests. Judge each declaration by the [value bar](../rules/test-value.md#value-bar)
and mark it per [ledger marks](../rules/test-value.md#ledger-marks).

The bar is high. An existing test is not deleted, merged, or repaired until its
entry records:

- the failure it can actually detect;
- the non-test callers of the code or seam it covers;
- the stronger proof that remains, or why no proof is needed;
- the history: why the test or seam exists;
- the production or test-support code its removal unlocks;
- the risk, and a focused validation command.

A missing field keeps the test. So does the
[retention bar](../rules/test-value.md#retention-bar): static or slow is never
the reason.

## Layer plan

Treat the ledgers as input, not as the edit list. Starting from them, look for
the redundant layer: several suites replaying one shared owner through a
mocked collaborator around a stronger real-boundary suite. Name the keeper for
each contract, preferring the real boundary with a fake external system over a
mocked collaborator. Correct any ledger error this finds.

The plan names, per lane, the retired tests, the keeper per contract, the
assertions carried into keepers, and the test-only seams unlocked.

## Edits

One writer applies the plan, one lane at a time:

- delete the test-only exports, flags, reset functions, wrappers, and dead
  production paths each lane unlocks, instead of keeping aliases;
- move retained regressions to their canonical owners;
- consolidate repeated assertions into one `parametrize` table or keeper;
- prefer net-negative production code, and add no replacement test that
  restates the same implementation;
- leave an uncertain candidate in place rather than deleting it to raise the
  count.

## Mutation proof

Required whenever the audit deleted or merged a test. For each owner function
whose contract moved:

```bash
uv run --with mutmut mutmut run "<dotted.module.function>*"
uv run --with mutmut mutmut results
uv run --with mutmut mutmut show <mutant-name>
```

- mutmut copies the sources into `mutants/` and never edits the checkout.
- `mutmut run` exits zero even when mutants survive, so read `mutmut results`
  for survivors instead of the exit code.
- Run one mutmut process per checkout at a time.
- Delete `mutants/` afterwards unless the project already ignores it.

mutmut changes operators, constants, arguments, and keywords; it never removes
a whole block. When a moved contract is a block of behavior, the recheck
confirms by reading that the keeper asserts it.

## Recheck

Read-only, in a fresh context that never saw the deletion reasoning. The input
is the lane's diff and the mutmut survivors. For every contract a removed or
merged test carried, find the keeper that still asserts it and record it as an
`R` entry whose `remaining_proof` names the keeper and how the contract was
confirmed: a killed mutant or, for a block of behavior, the assertion read in
the keeper. A contract with no keeper is a gap. A surviving mutant is a gap
unless it is shown to be equivalent. Also flag any new keeper assertion that
cannot fail.

Every gap is restored or rejected with source evidence, then rechecked.

## Product defects

A baseline failure that survives into a keeper is a bug report. Fix it at its
owner in a separate commit, with a regression test that fails on the unfixed
code. Record unrelated product discrepancies as follow-ups instead of fixing
them in the audit.

## Validation

1. Run the owner and sibling tests of every changed lane.
2. Run `git diff --check`.
3. Run `git diff --numstat` and count production and test lines separately.

## Handoff

The handoff records the scope, lanes, baseline, removed junk categories, owner
simplifications, retained false positives with the reason each stays, mutation
results, the proof commands actually run, production and test line counts, the
ledger files, and named follow-ups. It also proposes durable test-ownership
rules for the project's agent instructions, drawn only from mistakes this audit
actually found.
