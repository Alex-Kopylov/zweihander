# SGR Real-World Examples

## Table of Contents

1. [Math Reasoning](#math-reasoning)
2. [Text-to-SQL](#text-to-sql)
3. [Document Classification](#document-classification)
4. [Compliance Analysis](#compliance-analysis)
5. [Customer Support Triage](#customer-support-triage)
6. [Code Review](#code-review)

---

## Math Reasoning

Force the model to show work step-by-step before giving the final answer. The extra tokens spent on explanation improve accuracy significantly.

```python
from pydantic import BaseModel, Field

class ReasoningStep(BaseModel):
    explanation: str = Field(
        description="Explain what this step does and why"
    )
    output: str = Field(
        description="Result of this step (formula, intermediate value, etc.)"
    )

class MathReasoning(BaseModel):
    problem_restatement: str = Field(
        description="Restate the problem in your own words to confirm understanding"
    )
    steps: list[ReasoningStep] = Field(
        min_length=1,
        description="Step-by-step solution, each building on the previous"
    )
    final_answer: str = Field(
        description="The final numerical or symbolic answer"
    )
```

**Usage with OpenAI:**

```python
from openai import OpenAI

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Solve math problems step by step."},
        {"role": "user", "content": "A store has a 25% off sale. An item costs $80. You have a $10 coupon applied after the discount. What do you pay?"},
    ],
    response_format=MathReasoning,
)

result = response.choices[0].message.parsed
# result.steps contains the reasoning chain
# result.final_answer contains the answer
# Verify: 80 * 0.75 - 10 = 50.0 (compute in Python, don't trust the LLM)
```

---

## Text-to-SQL

The `strategy` field forces the model to plan before writing SQL. This single throwaway field improves accuracy by ~6%.

```python
from pydantic import BaseModel, Field
from typing import Literal

class TextToSQL(BaseModel):
    """Strategy field primes SQL generation — discard it after inference."""
    understanding: str = Field(
        description="What data is the user asking for? Restate in precise terms."
    )
    relevant_tables: str = Field(
        description="Which tables contain the needed data, and their key columns"
    )
    join_strategy: str = Field(
        description="How to connect tables: join type, conditions, cardinality"
    )
    filter_and_aggregation: str = Field(
        description="WHERE conditions, GROUP BY, HAVING, ORDER BY if needed"
    )
    sql_query: str = Field(
        description="Complete, executable SQL query"
    )
    query_dialect: Literal["postgresql", "mysql", "sqlite", "mssql"] = Field(
        description="SQL dialect used"
    )
```

**Why it works:** By the time the model reaches `sql_query`, it has already committed to specific tables, joins, and filters. The query practically writes itself — the model just assembles what it already decided.

---

## Document Classification

Uses Literal constraints to restrict classification to valid categories. Field ordering forces the model to summarize and extract entities before classifying — the early fields prime the classification even though you might discard them.

```python
from pydantic import BaseModel, Field
from typing import Literal

DOCUMENT_TYPES = [
    "contract", "invoice", "report", "memo",
    "proposal", "legal_notice", "correspondence",
]

ENTITY_TYPES = [
    "person", "organization", "date", "monetary_amount",
    "legal_reference", "product", "location",
]

class DocumentClassification(BaseModel):
    # Throwaway fields — force the model to read carefully before classifying
    document_type: Literal[tuple(DOCUMENT_TYPES)] = Field(
        description="Primary document category"
    )
    brief_summary: str = Field(
        description="2-3 sentence summary of the document's purpose and content"
    )
    key_entities: list[
        Literal[tuple(ENTITY_TYPES)]
    ] = Field(
        description="Entity types mentioned in the document"
    )
    keywords: list[str] = Field(
        max_length=10,
        description="Up to 10 keywords describing this document"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Classification confidence based on document clarity"
    )
```

**Testing this schema:**

```python
def test_document_classification(result: DocumentClassification):
    assert result.document_type in DOCUMENT_TYPES
    assert all(e in ENTITY_TYPES for e in result.key_entities)
    assert len(result.keywords) <= 10
    assert len(result.brief_summary) > 20
```

---

## Compliance Analysis

A multi-stage reasoning pipeline that addresses a real problem: compliance checks tend to be too pessimistic. The post-answer verification fields let the model reconsider severity after making its initial assessment.

```python
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from annotated_types import MinLen, MaxLen

class Applicability(BaseModel):
    """Reusable scoping check — determines if a requirement applies."""
    requirement_id: str = Field(description="Regulation clause ID")
    applies: bool = Field(description="Does this requirement apply to the entity?")
    reasoning: str = Field(description="Why it does or doesn't apply")

class ComplianceAnalysis(BaseModel):
    # Stage 1: Scope — which requirements apply
    entity_context: str = Field(
        description="Entity type, jurisdiction, and relevant business activities"
    )
    applicability_checks: Annotated[list[Applicability], MinLen(1), MaxLen(10)] = Field(
        description="Check each relevant requirement for applicability"
    )

    # Stage 2: Gap identification — mental notes before deciding
    identified_gaps: list[str] = Field(
        min_length=0,
        description="Preliminary gap notes — observations before formal assessment"
    )

    # Stage 3: Decision
    compliance_status: Literal["compliant", "non_compliant", "partially_compliant"] = Field(
        description="Overall compliance determination"
    )

    # Stage 4: Post-answer verification — reconsider severity
    noncompliance_category: Literal[
        "documentation", "process", "technical", "organizational", "none"
    ] = Field(
        description="Primary category of noncompliance, if any"
    )
    gap_severity: Literal["minor", "moderate", "critical", "not_applicable"] = Field(
        description="Reconsider: how severe are the identified gaps really?"
    )

    # Stage 5: Evidence grounding
    supporting_references: list[str] = Field(
        min_length=0,
        description="Specific regulation chapters, clauses, or sections cited"
    )
```

**Key insight on field naming:** the field `noncompliance_category` forces the model to recategorize after its initial assessment. Placing it after `compliance_status` creates a natural verification checkpoint — the model revisits its reasoning and often downgrades false-positive severity flags.

---

## Customer Support Triage

Combines Cascade (understand → classify) with Routing (branch by issue type) and Cycle (action items).

```python
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from annotated_types import MinLen, MaxLen

class ActionStep(BaseModel):
    step: str = Field(description="What to do")
    requires_escalation: bool = Field(
        description="Does this step need a human specialist?"
    )

class BillingIssue(BaseModel):
    category: Literal["billing"] = "billing"
    charge_type: Literal["subscription", "one_time", "refund", "dispute"]
    amount_mentioned: str | None = None
    resolution_path: str

class TechnicalIssue(BaseModel):
    category: Literal["technical"] = "technical"
    component: str = Field(description="Which product/feature is affected")
    error_description: str
    workaround_available: bool

class AccountIssue(BaseModel):
    category: Literal["account"] = "account"
    issue_type: Literal["access", "security", "profile", "deletion"]
    urgency: Literal["low", "medium", "high"]

class SupportTriage(BaseModel):
    # Cascade: understand before classifying
    customer_intent: str = Field(
        description="What is the customer actually trying to accomplish?"
    )
    sentiment: Literal["frustrated", "neutral", "positive"] = Field(
        description="Customer's emotional state"
    )
    # Routing: branch by issue type
    issue: BillingIssue | TechnicalIssue | AccountIssue = Field(
        discriminator="category"
    )
    # Cycle: bounded action plan
    recommended_actions: Annotated[list[ActionStep], MinLen(1), MaxLen(5)]
    # Cascade: final assessment
    estimated_resolution: Literal["immediate", "same_day", "escalation_needed"]
```

---

## Code Review

Uses Cascade to force analysis before verdict, Cycle for structured findings.

```python
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from annotated_types import MinLen, MaxLen, Ge, Le

class Finding(BaseModel):
    location: str = Field(description="File path and line range")
    category: Literal[
        "bug", "security", "performance", "readability",
        "testing", "architecture", "style",
    ]
    severity: Literal["info", "warning", "error", "critical"]
    description: str = Field(description="What the issue is")
    suggestion: str = Field(description="How to fix it")

class CodeReview(BaseModel):
    # Cascade: understand the change
    change_summary: str = Field(
        description="What this diff does and why, in 2-3 sentences"
    )
    change_scope: Literal["trivial", "moderate", "significant", "architectural"] = Field(
        description="Scale of the change relative to the codebase"
    )
    # Cascade: assess test coverage
    test_coverage_assessment: str = Field(
        description="Are the changes adequately tested? What's missing?"
    )
    # Cycle: structured findings
    findings: Annotated[list[Finding], MinLen(0), MaxLen(15)]
    # Cascade: overall verdict
    quality_score: Annotated[int, Ge(1), Le(10)] = Field(
        description="Overall code quality: 1=reject, 5=acceptable, 10=excellent"
    )
    verdict: Literal["approve", "request_changes", "comment_only"] = Field(
        description="Review decision based on findings and quality score"
    )
```
