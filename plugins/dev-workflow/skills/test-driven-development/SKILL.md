---
name: test-driven-development
description: Use when user asks to do TDD, test-first development, or red-green-refactor
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
  "references/testing-anti-patterns.md": "Load when the test needs mocks, test doubles, or test-only helpers."
  "references/rationalizations.md": "Load when anyone argues for skipping the failing test or writing tests after the code."
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you did not watch the test fail, you do not know if it
tests the right thing.

Violating the letter of the rules is violating the spirit of the rules.

## Ownership

This skill owns the language-neutral test-first process: the iron law, the
existing code gate, the RED-GREEN-REFACTOR loop, and the references listed in
the frontmatter.

Language-specific test selection, file layout, fixtures, and test authoring
belong to the matching language skill. For Python, invoke
`python-dev-workflow:tests-manager` and follow its rules instead of restating
them here. For every other language, follow the project's existing test
conventions.

## When to Use

Use for new features, bug fixes, refactoring, and behavior changes.

Ask your human partner before skipping TDD for throwaway prototypes, generated
code, or configuration files.

Thinking "skip TDD just this once"? That is rationalization. Load
`references/rationalizations.md`.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Reference Loading

Use the frontmatter metadata as the routing table. Load only the reference whose
metadata value matches the current task, and skip the rest.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it and implement fresh from the test. Do not
keep it as reference, do not adapt it while writing the test, and do not look at
it. Delete means delete.

## Existing Code Gate

Before choosing a test:

1. Inspect the callers and existing tests for the behavior being changed.
2. If an existing test owns that contract, update it for the intended behavior.
   Do not add a parallel ad hoc test just to create RED.
3. If coverage is missing, add the focused case to the nearest responsible test
   suite and follow its existing conventions.
4. For a behavior-preserving refactor with adequate coverage, use the existing
   tests unchanged: verify the focused suite is green, refactor, then keep it
   green. Do not invent a failing test for unchanged behavior.

## Outside-In Test Levels

When a behavior needs multiple test levels, work one scenario at a time and
author selected coverage from the outside in:

```text
E2E → Integration → Unit
```

Skip a level when it adds no distinct evidence. Keep each selected level in its
own RED-GREEN-REFACTOR cycle, and do not implement lower-level behavior before
its higher-level test is written.

## Red-Green-Refactor

The cycle applies to one scenario at one level.

### RED - Write A Failing Test

Cover one coherent behavior. Name the test after that behavior. Use real code;
mock only when unavoidable.

### Verify RED - Watch It Fail

Mandatory. Run the focused test and confirm three things:

- It fails rather than errors.
- The failure message is the one you expected.
- It fails because the behavior is missing, not because of a typo.

Test passed? You are testing existing behavior. Fix the test.

Test errored? Fix the error and re-run until it fails correctly.

### GREEN - Write Minimal Code

Write the simplest code that passes the test. Do not add options, features, or
improvements the test does not require.

### Verify GREEN - Watch It Pass

Mandatory. Run the focused test and confirm the test passes, the other tests
still pass, and the output is clean.

Test still fails? Fix the code, not the test.

### REFACTOR - Clean Up

Only after green. Remove duplication, improve names, extract helpers. Keep the
tests green and add no behavior.

## Good Tests

| Quality | Good | Bad |
|---|---|---|
| Minimal | One coherent behavior. Split independently meaningful failures. | `test('validates email and domain and whitespace')` |
| Clear | The name describes the behavior | `test('test1')` |
| Shows intent | Demonstrates the desired API | Hides what the code should do |

## Debugging Integration

Found a bug? Write the failing test that reproduces it, then run the cycle. The
test proves the fix and prevents the regression. Never fix a bug without a test.

## Verification Checklist

Before marking work complete:

- [ ] Changed behavior is covered by the responsible suite
- [ ] Selected levels were authored E2E → Integration → Unit
- [ ] Watched each test fail before implementing
- [ ] Each test failed for the expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass and the output is clean
- [ ] Tests use real code, with mocks only where unavoidable
- [ ] Edge cases and error paths are covered

Cannot check every box? You skipped TDD. Start over.

## When Stuck

| Problem | Solution |
|---|---|
| Do not know how to test | Write the wished-for API, then the assertion. Ask your human partner. |
| Test too complicated | The design is too complicated. Simplify the interface. |
| Must mock everything | The code is too coupled. Use dependency injection. |
| Test setup is huge | Extract helpers. Still complex? Simplify the design. |

## Final Rule

```
Production code → a test exists and failed first
Otherwise → not TDD
```

No exceptions without your human partner's permission.
