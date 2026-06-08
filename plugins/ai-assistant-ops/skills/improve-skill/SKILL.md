---
name: improve-skill
description: Use when revising an existing skill from eval feedback, trigger misses, output regressions, bloat, overfitting, or repeated manual work across skill runs.
---

# Improve Skill

Improve skills through measured iterations: test, compare, feedback, revise,
rerun, repeat, then tune triggering.

## Start Point

Start from the target skill and current stage: test prompts, baseline runs,
feedback review, rewriting, rerun comparison, or trigger checks. If the target
skill is unclear, resolve it before editing.

Require test prompts before editing. If no evals exist, create a small realistic
set first. Use objective assertions only for observable behavior; keep
subjective quality checks qualitative.

## Iteration Loop

1. Snapshot the target skill as the old-skill baseline.
2. Run the old-skill baseline and the candidate improved skill against the same
   prompts; keep inputs, target files, and expected outputs identical.
3. Capture outputs, transcripts, qualitative feedback, objective assertions when
   useful, timing and token data when available, and iteration history.
4. Compare the improved run against the old-skill baseline or previous
   iteration, whichever best answers the user's current question.
5. Revise from feedback by generalizing the lesson. Do not overfit wording to
   one prompt, hide behavior behind rigid commands, or add instructions that do
   not earn their tokens.
6. Keep the prompt lean. Remove unused guidance, repeated wording, and
   unproductive transcript-driven detours.
7. Explain why important instructions matter so the next assistant can adapt
   rather than follow brittle rules by rote.
8. Look for repeated manual work across test cases. If multiple runs recreate a
   helper, checklist, schema, or conversion step, add a reusable `scripts/` tool
   or resources file and point the skill to it.
9. After rewriting, invoke `ai-assistant-ops:md-bloat-hunter` on the changed
   skill context before evaluation or rerun. Preserve behavior and
   trigger coverage while removing redundancy and filler.
10. Review the draft with fresh eyes; tighten unsupported wording.
11. Rerun all test cases with baseline runs into the next iteration, compare
    against the previous iteration, and wait for the user to review results.
12. Read the reviewed feedback before the next rewrite.

Repeat until the user is satisfied, feedback is empty, or progress stalls.
When progress stalls, ask whether to change the eval set, accept the tradeoff,
or stop.

## Evidence To Keep

Keep evidence for each iteration: target and snapshot paths, prompt set,
old-skill and improved outputs, transcript notes, feedback, assertions, timing
or token data, and what changed with why.

## Trigger Optimization

After the body stabilizes, test the description with should-trigger and
should-not-trigger prompts, including near misses. Revise it only for missed
triggers or false positives.

Keep the description trigger-only: symptoms and situations, not workflow.

## Mistakes

| Mistake | Correction |
|---|---|
| Editing before evals exist | Create prompts first. |
| Comparing different prompt sets | Use the same prompts. |
| Treating one complaint as a patch | Generalize. |
| Adding prose for every failure | Prefer lean wording, examples, scripts, or resources. |
| Stopping after body edits | Run trigger checks. |
