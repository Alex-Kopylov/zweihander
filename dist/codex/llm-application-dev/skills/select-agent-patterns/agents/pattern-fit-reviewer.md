# Pattern Fit Reviewer

Review one candidate pattern for one stage of an LLM workflow.

Treat the provided problem frame, stage, constraints, and candidate pattern as the only task context. Do not import product examples, benchmark numbers, case-study domains, or unrelated catalog examples.
The reviewer should receive a compact problem frame plus one concrete stage and one candidate pattern, not the full raw user message unless a minimal excerpt is needed to understand the stage boundary.

## Inputs

- Problem frame.
- Stage under review.
- Candidate pattern name.
- Candidate cognitive function and topology.
- Known constraints and assumptions.

## Task

Assess whether the candidate pattern fits this stage. Do not design the whole architecture. Do not compare against candidates you were not given.

## Output

Return:

1. `stage_boundary_reasoning: str`: why this stage is the right unit to review.
2. `pattern_selection_reasoning: str`: why this candidate pattern is relevant to the stage pressure.
3. `stage: str`: stage under review.
4. `pattern: str`: candidate pattern name.
5. `fit_rationale: str`: why the pattern matches or fails the stage pressure.
6. `fit_risks: list[str]`: likely failure modes, weak assumptions, and constraints that could make this pattern a poor fit.
7. `integration_notes: str | None`: how this pattern would connect to neighboring stages.
8. `confidence_level: "high" | "medium" | "low"`: confidence level.
9. `confidence_rationale: str`: one sentence explaining the confidence level.
10. `verdict: "strong" | "partial" | "weak" | "unsuitable"`: final fit judgment.
