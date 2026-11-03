# Write Step

One step: add or change tests, and the production code they drive, test first.

## Existing code gate

Before choosing a test:

1. Read the callers and existing tests of the behavior being changed.
2. If an existing test owns that contract, update it for the intended behavior.
   Do not add a parallel test just to create RED.
3. If coverage is missing, add the case to the nearest responsible test module
   and follow its conventions.
4. For a behavior-preserving refactor with adequate coverage, keep the existing
   tests unchanged: confirm they pass, refactor, and keep them passing. Do not
   invent a failing test for unchanged behavior.

## Level selection

Skip this section when a level was assigned to you.

| Level | Owns | Select when |
|---|---|---|
| E2E | Externally observable business behavior across the complete system boundary | A user or external consumer must complete a real journey |
| Integration | Routes, dependency injection, services, queries, resources, and lifecycle wiring | Correctness depends on components working together |
| Unit | Local decisions no other layer owns | Correctness can be isolated from system wiring |

Select only the levels that add distinct evidence. Judge completeness by
proven requirement-linked scenarios and corner cases, not by test count or
code-coverage percentage. A branch needs a unit test only when no test at any
layer owns it.

Author selected levels from the outside in, one scenario at a time:

```text
E2E → Integration → Unit
```

Run the full cycle below at each selected level before moving inward. Load the
level reference for each level you write: [unit](../levels/unit.md),
[integration](../levels/integration.md), [E2E](../levels/e2e.md).

## Authoring gate

Before adding or changing a test, answer each question. A missing answer means
the test is not added.

1. Which contract does it protect, and which credible regression makes it fail?
2. Why does existing coverage not already catch that regression?
3. Does it need a production seam — an export, flag, wrapper, or injection
   hook — that no production caller needs? If so, test at the real boundary
   instead.
4. Does it match a [junk pattern](../rules/test-value.md#junk-patterns)? A
   match fails the gate unless the
   [retention bar](../rules/test-value.md#retention-bar) names the contract it
   independently guards.
5. Would it survive a behavior-preserving refactor? If not, it asserts
   implementation; rewrite it at the owning boundary.

A bug fix adds one regression test at the owner boundary: the layer where the
cause lives, not every layer the bug crosses. That test fails on the pre-fix
code for the intended reason.

## Red-green-refactor

Production code without a failing test first is deleted and rewritten from the
test. Do not keep it as a reference or adapt it while writing the test. When
anyone argues for skipping this, see
[rationalizations](../rules/rationalizations.md).

### RED

Write one test for one coherent behavior, named after that behavior. Use real
code; use a double only at a [mocking boundary](../rules/mocking.md#boundaries).

### Verify RED

Run the focused test and confirm that it fails rather than errors, with the
expected message, because the behavior is missing. A test that passes already
tests existing behavior: fix the test. A test that errors: fix the error and
run it again.

### GREEN

Write the simplest code that passes. Add no options or features the test does
not require.

### Verify GREEN

Run the focused test and its neighbours. All pass and the output is clean. If
the test still fails, fix the code, not the test.

### REFACTOR

Only when green: remove duplication, improve names, extract helpers. Keep the
tests green and add no behavior.

## When stuck

| Problem | Response |
|---|---|
| Unsure how to test it | Write the wished-for API call, then the assertion. Ask the user. |
| The test is complicated | The design is complicated. Simplify the interface. |
| Everything must be mocked | The code is too coupled. Inject the dependency. |
| The setup is huge | Extract fixtures or builders. Still huge? Simplify the design. |

## Checklist

- Each test failed first, for the expected reason, before its code was written.
- Each test passed the authoring gate.
- Every changed behavior has proof at the level that owns it, and no two levels
  prove the same thing.
- Each bug fix has one regression test that fails on the old code.
- Names, paths, fixtures, and builders follow the
  [conventions](../rules/conventions.md).
- The focused pytest command ran clean, or the reason it could not run is
  reported.
