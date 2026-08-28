# Rationalizations

**Load this reference when:** you or the user argue for skipping the failing
test, writing tests after the code, or keeping untested code as reference.

## Red Flags - Stop and Start Over

- Code before test
- Test after implementation
- Test passes immediately
- Cannot explain why the test failed
- Tests added "later"
- "Just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It is about spirit, not ritual"
- "Keep as reference" or "adapt existing code"
- "Already spent hours, deleting is wasteful"
- "TDD is dogmatic, I am being pragmatic"
- "This is different because..."

All of these mean the same thing: delete the code and start over with TDD.

## Counterarguments

| Excuse | Reality |
|---|---|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I will test after" | A test that passes immediately proves nothing. |
| "Tests after achieve the same goals" | Tests-after answer "what does this do?" Tests-first answer "what should this do?" |
| "Already manually tested" | Ad-hoc is not systematic. No record, cannot re-run. |
| "Deleting hours of work is wasteful" | Sunk cost. Keeping unverified code is technical debt. |
| "Keep it as reference" | You will adapt it. That is testing after. Delete means delete. |
| "I need to explore first" | Explore, then throw the exploration away and start with TDD. |
| "Hard to test means the test is wrong" | Hard to test means hard to use. Listen to the test. |
| "TDD will slow me down" | TDD is faster than debugging what you cannot reproduce. |
| "Manual testing is faster" | Manual testing misses edge cases and repeats every change. |
| "Existing code has no tests" | You are improving it. Add the tests. |

## Why Order Matters

Tests written after the code pass immediately, and passing immediately proves
nothing: the test may check the wrong thing, may check the implementation
instead of the behavior, and never caught a real bug. Writing the test first
forces you to watch it fail, which is the only evidence that it tests anything.

Tests-after are also biased by the implementation. You verify the edge cases you
remember, not the ones you would have discovered while designing the test.
