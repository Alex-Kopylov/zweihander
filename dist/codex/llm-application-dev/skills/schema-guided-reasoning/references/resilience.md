# SGR Resilience — Handling Partial LLM Output

## The Problem

LLMs sometimes produce partial structured output — they might skip a field, truncate mid-response, or return malformed JSON. Standard Pydantic validation rejects the entire response if any required field is missing. In production, a partial answer is almost always better than no answer.

SGR schemas are especially affected because they have many fields (reasoning + output + evals + final_output). The more fields, the higher the chance the model skips one.

---

## TBDBaseModel Pattern

A Pydantic base class that defaults any missing field to `"TBD"` instead of raising a `ValidationError`. All reasoning and eval models inherit from this.

```python
from pydantic import BaseModel, model_validator


class TBDBaseModel(BaseModel):
    """Base model that fills missing fields with 'TBD' instead of failing.

    Reasoning and eval schemas inherit from this so partial LLM output
    doesn't crash the pipeline. 'TBD' fields are visible in traces and
    dashboards, making gaps obvious without losing the rest of the response.
    """

    @model_validator(mode="before")
    @classmethod
    def fill_missing_with_tbd(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        for field_name, field_info in cls.model_fields.items():
            if field_name not in data or data[field_name] is None:
                data[field_name] = "TBD"
        return data
```

### Usage

```python
class PolicyReasoning(TBDBaseModel):
    control_requirements: str = Field(
        description="Key requirements from the control family"
    )
    implementation_context: str = Field(
        description="How requirements map to the target organization"
    )

# If the LLM skips implementation_context:
# {"control_requirements": "AC family requires..."}
# → PolicyReasoning(control_requirements="AC family requires...", implementation_context="TBD")
# Instead of: ValidationError
```

---

## TBDType Sentinel

To distinguish "model skipped this field" from "model returned an empty string", use a dedicated sentinel type:

```python
from typing import Literal


class _TBDMeta(type):
    def __instancecheck__(cls, instance: object) -> bool:
        return isinstance(instance, str) and instance == "TBD"

    def __repr__(cls) -> str:
        return "TBDType"


class TBDType(str, metaclass=_TBDMeta):
    """Sentinel for fields the LLM didn't fill."""
    pass


def is_tbd(value: object) -> bool:
    """Check if a value is the TBD sentinel."""
    return isinstance(value, str) and value == "TBD"
```

### Field type annotations with TBDType

```python
class PolicyEvals(TBDBaseModel):
    # Field is either a real answer or TBD — type union makes this explicit
    completeness: str | TBDType = Field(
        description="PASS if all requirements addressed, else FAIL with gaps"
    )
    specificity: str | TBDType = Field(
        description="PASS if org-specific, else FAIL if generic"
    )
```

---

## Stricter Eval Fields

Free-form `str` eval fields let the model write anything. Use `Literal["PASS", "FAIL"]` with a `TBDType` fallback for eval fields — this constrains the model to a clear verdict while remaining resilient to partial output:

```python
class PolicyEvalsStrict(TBDBaseModel):
    completeness: Literal["PASS", "FAIL"] | TBDType = Field(
        description="PASS if all requirements addressed, else FAIL"
    )
    specificity: Literal["PASS", "FAIL"] | TBDType = Field(
        description="PASS if org-specific, else FAIL"
    )
    actionability: Literal["PASS", "FAIL"] | TBDType = Field(
        description="PASS if policy has clear directives, else FAIL"
    )
```

**Why this matters:** With `Literal["PASS", "FAIL"]`, constrained decoding forces the model to commit to one verdict — no hedging like "mostly passes" or "partially fails." The `TBDType` fallback ensures partial output still parses.

This also makes downstream processing trivial:

```python
def is_passing(value: str) -> bool:
    """Check if an eval field passed."""
    return isinstance(value, str) and value.startswith("PASS")
```

---

## Partial JSON Deserialization

When the LLM response is truncated mid-JSON, standard `json.loads()` fails. Use Pydantic's `allow_partial` mode to salvage what you can:

```python
import pydantic_core


def parse_llm_response(
    raw: str,
    response_type: type[BaseLLMResponse],
) -> BaseLLMResponse | None:
    """Parse LLM JSON response, tolerating truncation."""
    try:
        # Try strict parse first
        return response_type.model_validate_json(raw)
    except Exception:
        pass

    try:
        # Fall back to partial parse — salvages truncated JSON
        partial_data = pydantic_core.from_json(raw, allow_partial=True)
        return response_type.model_validate(partial_data)
    except Exception:
        return None
```

This works well with `TBDBaseModel` — partial JSON produces a dict with missing keys, and the TBD validator fills them in.

---

## Complete Example

A production-grade resilient SGR response:

```python
from abc import ABC
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator


# --- Resilience base ---

class TBDBaseModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def fill_missing_with_tbd(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        for field_name in cls.model_fields:
            if field_name not in data or data[field_name] is None:
                data[field_name] = "TBD"
        return data


# --- SGR pipeline base ---

TOutput = TypeVar("TOutput", bound=BaseModel)
TReasoning = TypeVar("TReasoning", bound=BaseModel)
TEvals = TypeVar("TEvals", bound=BaseModel)


class BaseLLMResponse(BaseModel, ABC, Generic[TOutput, TReasoning, TEvals]):
    reasoning: TReasoning = Field(...)
    output: TOutput = Field(...)
    evals: TEvals = Field(...)
    final_output: TOutput | None = Field(default=None)

    @property
    def resolved_output(self) -> TOutput:
        return self.final_output if self.final_output is not None else self.output


# --- Domain schemas (reasoning and evals inherit TBDBaseModel) ---

class ComplianceReasoning(TBDBaseModel):
    regulation_scope: str = Field(
        description="Which regulatory requirements apply to this entity"
    )
    preliminary_assessment: str = Field(
        description="Initial compliance assessment before formal evaluation"
    )

class ComplianceEvals(TBDBaseModel):
    completeness: Literal["PASS", "FAIL"] | str = Field(
        description="PASS if all applicable requirements assessed"
    )
    evidence_grounded: Literal["PASS", "FAIL"] | str = Field(
        description="PASS if assessment cites specific regulation clauses"
    )

class ComplianceOutput(BaseModel):
    status: Literal["compliant", "non_compliant", "partial"]
    summary: str


# --- Concrete response type ---

ComplianceResponse = BaseLLMResponse[
    ComplianceOutput, ComplianceReasoning, ComplianceEvals
]
```

Now if the LLM truncates after `reasoning` and `output`, skipping `evals`:

```python
partial_json = '{"reasoning": {"regulation_scope": "NIST 800-53"}, "output": {"status": "compliant", "summary": "Meets requirements"}'

result = parse_llm_response(partial_json, ComplianceResponse)
# result.reasoning.regulation_scope == "NIST 800-53"
# result.reasoning.preliminary_assessment == "TBD"  ← filled by TBDBaseModel
# result.output.status == "compliant"
# result.evals.completeness == "TBD"  ← filled by TBDBaseModel
# result.final_output is None
# result.resolved_output.status == "compliant"  ← still usable
```
