---
name: schema-guided-reasoning
description: Use this skill when designing Pydantic models that guide LLM reasoning through structured output. Triggers include "schema-guided reasoning", "SGR", "structured reasoning schema", "pydantic structured output", "reasoning steps schema", "constrained decoding", "step-by-step schema", "LLM reasoning pipeline", "discriminated union for tool routing", "tool-calling schema design", or any situation where the user wants to improve LLM accuracy by defining the shape of the output. Also use when the user builds Pydantic models for OpenAI/Anthropic structured output and wants to maximize reasoning quality, designs agent tool dispatch with discriminated unions, or structures chain-of-thought via field ordering — even if they don't mention SGR by name.
model: opus
---

# Schema-Guided Reasoning (SGR)

Design Pydantic schemas that direct LLMs through predefined reasoning steps before producing a final answer. Instead of hoping the model reasons well in free text, you encode the expert's mental checklist into schema fields — then constrained decoding forces the model to fill every field in order.

## Why It Works

LLMs generate structured output field by field, left to right. Each field's value becomes context for the next. By ordering fields to mirror an expert's thought process, you turn the schema into a mandatory reasoning pipeline:

```
[field_1: understand the problem]
  → [field_2: analyze key factors]
    → [field_3: reach conclusion]
      → [field_4: verify conclusion]
```

The model cannot skip ahead to the conclusion — it must work through each step. This alone yields 5-10% accuracy improvements out of the box, especially with smaller or local models.

SGR supplements prompting — it does not replace it. The system prompt still provides context and instructions; the schema enforces *how* the model reasons through them.

## Three Core Patterns

### 1. Cascade — Sequential Reasoning

Force the model through ordered reasoning steps where each field builds on the previous.

```python
from pydantic import BaseModel, Field

class CandidateEval(BaseModel):
    """Each field forces deeper analysis before the decision."""
    brief_summary: str = Field(description="Summarize candidate background in 2-3 sentences")
    skill_match_score: int = Field(ge=1, le=10, description="Rate skill alignment with role requirements")
    culture_fit_notes: str = Field(description="Assess team and company culture alignment")
    recommendation: Literal["hire", "reject", "hold"] = Field(description="Final decision based on above analysis")
```

**Key insight**: field ordering IS the reasoning order. Put analysis before conclusions. Early fields can be "throwaway" — they exist purely to improve later fields and may be discarded after inference.

### 2. Routing — Branch Into Specific Paths

Force the model to classify first, then fill branch-specific fields using discriminated unions.

```python
class HardwareIssue(BaseModel):
    kind: Literal["hardware"] = "hardware"
    device_type: str
    warranty_status: str
    resolution: str

class SoftwareIssue(BaseModel):
    kind: Literal["software"] = "software"
    application: str
    error_code: str | None = None
    steps_to_reproduce: str

class TicketTriage(BaseModel):
    customer_summary: str = Field(description="Restate the customer's problem")
    issue: HardwareIssue | SoftwareIssue = Field(discriminator="kind")
```

The `Literal` discriminator forces the model to commit to one path. Once committed, it fills only that branch's fields — no confusion between paths.

### 3. Cycle — Repeated Structured Units (Optional)

When your domain needs multiple structured items — risk factors, action items, evidence entries — you can bound the list to prevent the model from being lazy (too few) or rambling (too many). Not every schema needs this; many start with simple flat fields and add Cycle later as the domain evolves.

```python
from annotated_types import MinLen, MaxLen
from typing import Annotated

class RiskFactor(BaseModel):
    factor: str = Field(description="Identified risk")
    explanation: str = Field(description="Why this is a risk in context")
    severity: Literal["low", "medium", "high", "critical"]
    mitigation: str = Field(description="Recommended mitigation step")

class RiskAssessment(BaseModel):
    context_summary: str  # Cascade: understand first
    risks: Annotated[list[RiskFactor], MinLen(2), MaxLen(5)]  # Cycle: bounded repetition
    overall_risk_level: Literal["acceptable", "elevated", "critical"]  # Cascade: conclude last
```

Use `MinLen`/`MaxLen` from `annotated_types` when you have clear bounds; otherwise start with a plain `list[T]`.

## Combining Patterns

Patterns compose naturally. The most powerful schemas use all three:

```python
class NextStep(BaseModel):
    """Cascade + Cycle + Routing in one schema."""
    current_state: str                                                    # Cascade: reflect
    plan: Annotated[list[str], MinLen(1), MaxLen(5)]                     # Cycle: plan ahead
    task_completed: bool                                                  # Cascade: check
    action: SendEmail | SearchDB | CreateInvoice | ReportDone            # Routing: dispatch
```

This is the **adaptive planning** pattern — the model reflects on state, plans ahead, then routes to the right tool. See `references/adaptive-planning.md` for the full agent loop.

## Self-Correction Pipeline

The patterns above guide reasoning toward a single output. In production, you often want the model to also evaluate and correct its own work — within a single structured output call. This extends SGR's "post-answer verification" into a full self-correction loop.

### The Generic Base

A reusable base class parameterized by output, reasoning, and eval types:

```python
from abc import ABC
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

TOutput = TypeVar("TOutput", bound=BaseModel)
TReasoning = TypeVar("TReasoning", bound=BaseModel)
TEvals = TypeVar("TEvals", bound=BaseModel)


class BaseLLMResponse(BaseModel, ABC, Generic[TOutput, TReasoning, TEvals]):
    """SGR pipeline: reason → produce → evaluate → self-correct."""

    reasoning: TReasoning = Field(
        ..., description="Structured reasoning before producing output."
    )
    output: TOutput = Field(..., description="Initial output.")
    evals: TEvals = Field(
        ..., description="Self-evaluation checks against the initial output."
    )
    final_output: TOutput | None = Field(
        default=None,
        description="Corrected output if any evals failed. Omit if all evals pass.",
    )

    @property
    def resolved_output(self) -> TOutput:
        """Return corrected output if available, otherwise the initial one."""
        return self.final_output if self.final_output is not None else self.output
```

The field order enforces the cascade: the model must reason before outputting, output before evaluating, and evaluate before deciding whether to correct. The `resolved_output` property gives callers a single access point — they never need to know whether self-correction happened.

### Opt-Out Sentinels

Not every task needs all stages. Sentinel types let you skip reasoning or evals without changing the base class:

```python
class NoReasoning(BaseModel):
    placeholder: str | None = Field(default=None, description="Omit reasoning.")

class NoEvals(BaseModel):
    placeholder: str | None = Field(default=None, description="Omit evals.")
```

### Concrete Example

A content generation pipeline with reasoning and self-checks:

```python
class PolicyReasoning(BaseModel):
    control_requirements: str = Field(
        description="Key requirements from the control family"
    )
    implementation_context: str = Field(
        description="How requirements map to the target organization"
    )
    generation_approach: str = Field(
        description="Strategy for structuring the policy content"
    )

class PolicyEvals(BaseModel):
    completeness: str = Field(
        description="PASS if all requirements addressed, else FAIL with gaps"
    )
    specificity: str = Field(
        description="PASS if org-specific, else FAIL if generic boilerplate"
    )
    actionability: str = Field(
        description="PASS if policy has clear directives, else FAIL"
    )

class PolicyOutput(BaseModel):
    value: str = Field(description="Generated policy content")


# Full pipeline — reasoning guides output, evals enable self-correction
PolicyResponse = BaseLLMResponse[PolicyOutput, PolicyReasoning, PolicyEvals]

# Lightweight variant — when the task is simple enough, skip the overhead
SimplePolicyResponse = BaseLLMResponse[PolicyOutput, NoReasoning, NoEvals]
```

See `references/resilience.md` for handling partial LLM output with TBDBaseModel, and `references/observability.md` for publishing eval results to Langfuse.

## Design Principles

### Field Naming Matters

The field name is copied to the output prompt token-by-token before the model generates the value. Descriptive names prime the model better than generic ones:

```python
# Weak — generic name gives no reasoning direction
notes: str

# Strong — name itself guides what the model should think about
reasoning_about_regulatory_compliance: str
```

### Throwaway Fields Improve Accuracy

Fields that exist only to force reasoning — not for your final output — are a core SGR technique. The text-to-SQL pattern adds a `strategy` field before `sql_query` that increases accuracy by 6%, even though you discard `strategy` after inference.

```python
class TextToSQL(BaseModel):
    strategy: str = Field(description="Identify tables, joins, and filters needed")
    sql_query: str = Field(description="The SQL query")
```

### Schema-Enforced Constraints Replace Prompt Instructions

When a constraint is expressible in the type system, put it there — not in the prompt. Schema constraints are guaranteed by constrained decoding; prompt instructions are suggestions.

```python
# Prompt: "Never give more than 50% discount" — model might ignore this
# Schema: guaranteed by type system
discount_percent: Annotated[int, Ge(0), Le(50)]
```

Use `Ge`, `Le` from `annotated_types` for numeric bounds, `Literal` for enum constraints, `MinLen`/`MaxLen` for list bounds.

### Post-Answer Verification

If a reasoning pipeline tends toward false positives or negatives, add verification fields *after* the answer to let the model reconsider:

```python
class ComplianceCheck(BaseModel):
    preliminary_analysis: str          # Step 1: analyze
    gap_notes: list[str]               # Step 2: identify gaps
    compliance_status: Literal["compliant", "non_compliant", "partial"]  # Step 3: decide
    reason_for_noncompliance: str      # Step 4: verify — forces reconsideration
    severity: Literal["minor", "moderate", "critical"]                   # Step 5: calibrate
```

### Keep Math in Python

LLMs are unreliable at arithmetic. When your schema involves calculations (pricing, totals, percentages), compute in Python after extracting the structured data — never rely on the model to calculate correctly.

## Pattern Selection Guide

| Situation | Pattern | Why |
|-----------|---------|-----|
| Step-by-step analysis toward a conclusion | **Cascade** | Forces ordered reasoning |
| Classification / triage / branching | **Routing** | Commits to one path via discriminator |
| Multiple items with bounded count | **Cycle** | Prevents too few or too many |
| Agent tool dispatch | **Routing** (or Cycle + Routing) | Each tool is a union variant |
| Multi-step agent with planning | **All three** | Reflect → Plan → Check → Dispatch |
| Improving accuracy of a weak model | **Cascade** with throwaway fields | Extra reasoning tokens help |

## Testing SGR Outputs

Because SGR produces structured fields, each field is directly testable:

```python
def test_candidate_evaluation():
    result: CandidateEval = run_sgr(prompt="Evaluate this candidate...", schema=CandidateEval)

    assert 1 <= result.skill_match_score <= 10
    assert result.recommendation in ("hire", "reject", "hold")
    assert len(result.brief_summary) > 20  # Not trivially short
```

Put complexity in the schema fields, keep the final answer trivial, and embed grounding/evidence in intermediate fields — this makes evals reliable and debuggable.

## Reference Files

Read these for deeper examples and patterns:

- **`references/patterns.md`** — Full Pydantic V2 code for each pattern with variations and anti-patterns. Read when designing a new SGR schema from scratch.
- **`references/examples.md`** — Real-world use cases: math reasoning, text-to-SQL, document classification, compliance analysis. Read when you need a template for a specific domain.
- **`references/adaptive-planning.md`** — The NextStep agent loop pattern with tool dispatch, continuous replanning, and conversation context management. Read when building an agentic system with SGR.
- **`references/resilience.md`** — TBDBaseModel for handling partial LLM output: defaulting missing fields to "TBD" instead of failing validation, `Literal["PASS", "FAIL"] | TBDType` for stricter evals. Read when your SGR schemas need to survive real-world LLM unreliability.
- **`references/observability.md`** — Publishing SGR eval fields as Langfuse scores and reasoning as trace metadata. Read when you want quantitative quality tracking over your SGR pipelines.
