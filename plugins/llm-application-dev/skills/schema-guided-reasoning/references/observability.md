# SGR Observability — Langfuse Integration

## Why Observe SGR

SGR eval fields are structured PASS/FAIL verdicts the model generates about its own output. Publishing these to Langfuse turns self-evaluation into quantitative quality metrics — you can track pass rates per eval field, per model, per schema version, over time.

This answers questions like:
- "Is our compliance schema getting more accurate after the last prompt change?"
- "Which eval field fails most often — completeness or specificity?"
- "Does gpt-4o pass our evals more reliably than gpt-4o-mini?"

---

## Publishing Eval Scores

Each eval field becomes a Langfuse `BOOLEAN` score: `PASS` → 1.0, `FAIL` → 0.0, `TBD` → skipped.

```python
from langfuse import Langfuse

langfuse = Langfuse()


def publish_eval_scores(
    trace_id: str,
    evals: BaseModel,
    observation_id: str | None = None,
) -> None:
    """Publish each eval field as a Langfuse BOOLEAN score."""
    for field_name, value in evals.model_dump().items():
        if field_name == "placeholder":
            continue  # Skip NoEvals sentinel

        str_value = str(value)

        # Skip TBD fields — no score is better than a misleading one
        if str_value == "TBD":
            continue

        passed = str_value.startswith("PASS")

        langfuse.score(
            trace_id=trace_id,
            observation_id=observation_id,
            name=field_name,
            value=1.0 if passed else 0.0,
            data_type="BOOLEAN",
            comment=str_value if not passed else None,  # Attach failure reason
        )
```

**Key decisions:**
- `data_type="BOOLEAN"` — Langfuse renders these as pass/fail badges and aggregates them as pass rates
- `comment` only on failures — captures the model's explanation for why it failed, useful for debugging
- TBD fields are skipped — a missing score is honest; a fake 0.0 would pollute metrics

---

## Attaching Reasoning as Metadata

The reasoning dict provides the model's thought process. Attach it to the Langfuse trace for debugging — it's not a score, it's context.

```python
def publish_reasoning_metadata(
    trace_id: str,
    reasoning: BaseModel,
    observation_id: str | None = None,
) -> None:
    """Attach reasoning fields to trace metadata for debugging."""
    reasoning_dict = reasoning.model_dump()

    # Remove placeholder from NoReasoning sentinel
    if list(reasoning_dict.keys()) == ["placeholder"]:
        return

    langfuse.trace(
        id=trace_id,
        metadata={"sgr_reasoning": reasoning_dict},
    )
```

When investigating a failed eval in Langfuse, you can see what the model was "thinking": which reasoning fields were populated, which were TBD, and whether the reasoning supported the output.

---

## Complete Integration Example

Combining eval scores, reasoning metadata, and self-correction tracking:

```python
from langfuse import Langfuse

from schemas.commons.response import BaseLLMResponse

langfuse = Langfuse()


def publish_trace_observability(
    trace_id: str,
    parsed: BaseLLMResponse,
    observation_id: str | None = None,
) -> None:
    """Publish full SGR observability to Langfuse."""

    # 1. Publish eval scores
    evals_dict = parsed.evals.model_dump()
    for field_name, value in evals_dict.items():
        if field_name == "placeholder":
            continue

        str_value = str(value)
        if str_value == "TBD":
            continue

        passed = str_value.startswith("PASS")
        langfuse.score(
            trace_id=trace_id,
            observation_id=observation_id,
            name=field_name,
            value=1.0 if passed else 0.0,
            data_type="BOOLEAN",
            comment=str_value if not passed else None,
        )

    # 2. Attach reasoning as metadata
    reasoning_dict = parsed.reasoning.model_dump()
    if list(reasoning_dict.keys()) != ["placeholder"]:
        langfuse.trace(
            id=trace_id,
            metadata={"sgr_reasoning": reasoning_dict},
        )

    # 3. Track whether self-correction happened
    self_corrected = parsed.final_output is not None
    langfuse.score(
        trace_id=trace_id,
        observation_id=observation_id,
        name="self_corrected",
        value=1.0 if self_corrected else 0.0,
        data_type="BOOLEAN",
        comment="Model produced a corrected final_output" if self_corrected else None,
    )
```

### Usage in your LLM call pipeline

```python
async def generate_with_observability(
    prompt: str,
    response_type: type[BaseLLMResponse],
) -> BaseLLMResponse:
    """Generate structured output and publish observability."""
    trace = langfuse.trace(name="sgr-generation")

    generation = trace.generation(
        name="llm-call",
        model="gpt-4o",
        input=prompt,
    )

    # ... your LLM call here ...
    parsed = response_type.model_validate_json(raw_response)

    generation.end(output=parsed.resolved_output.model_dump())

    publish_trace_observability(
        trace_id=trace.id,
        parsed=parsed,
        observation_id=generation.id,
    )

    return parsed
```

---

## What You Can Track

With SGR eval fields published as Langfuse scores, you get:

| Metric | How | Use |
|--------|-----|-----|
| **Pass rate per eval field** | Langfuse score analytics by name | Find which quality dimensions fail most |
| **Pass rate per model** | Filter by model in Langfuse | Compare model performance on your criteria |
| **Self-correction rate** | `self_corrected` score | How often does the model catch its own mistakes |
| **Pass rate over time** | Langfuse time-series view | Track quality trends after prompt/schema changes |
| **Failure reasons** | Score comments | Debug why specific eval fields fail |
| **Reasoning quality** | Trace metadata inspection | See what the model "thought" on specific traces |

The eval field names in your schema become the score names in Langfuse automatically — so `completeness`, `specificity`, `actionability` show up as trackable metrics without extra configuration.
