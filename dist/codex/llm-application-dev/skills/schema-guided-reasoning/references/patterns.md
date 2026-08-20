# SGR Patterns — Full Reference

## Cascade Pattern

Forces sequential reasoning where each field builds on the previous. The model generates fields left-to-right — earlier field values become context for later ones.

### Basic Cascade

```python
from pydantic import BaseModel, Field
from typing import Literal

class InvestmentAnalysis(BaseModel):
    """Cascade: each field narrows toward the recommendation."""
    market_context: str = Field(
        description="Current market conditions relevant to this investment"
    )
    company_strengths: str = Field(
        description="Key competitive advantages and financial health indicators"
    )
    risk_factors: str = Field(
        description="Primary risks: regulatory, market, execution"
    )
    risk_reward_ratio: Literal["favorable", "neutral", "unfavorable"] = Field(
        description="Overall risk-reward assessment based on above analysis"
    )
    recommendation: Literal["strong_buy", "buy", "hold", "sell", "strong_sell"] = Field(
        description="Investment recommendation grounded in the analysis"
    )
```

### Cascade with Throwaway Fields

Fields that exist only to improve reasoning quality. Discard them after inference.

```python
class TextToSQL(BaseModel):
    """The strategy field is never used — it exists to prime the SQL generation."""
    relevant_tables: str = Field(
        description="Which tables are needed and their key columns"
    )
    join_strategy: str = Field(
        description="How tables connect: join conditions and cardinality"
    )
    filter_logic: str = Field(
        description="WHERE clause logic and edge cases to handle"
    )
    sql_query: str = Field(
        description="Complete SQL query implementing the above strategy"
    )

# After inference, use only result.sql_query
```

### Cascade with Numeric Scoring

Constrain scores to force calibrated assessment before the decision.

```python
from annotated_types import Ge, Le
from typing import Annotated

class ResumeScreening(BaseModel):
    experience_summary: str = Field(
        description="Relevant experience for this role"
    )
    technical_score: Annotated[int, Ge(1), Le(10)] = Field(
        description="Technical skills match: 1=no match, 10=perfect match"
    )
    communication_score: Annotated[int, Ge(1), Le(10)] = Field(
        description="Communication quality from resume/cover letter"
    )
    overall_fit: Annotated[int, Ge(1), Le(10)] = Field(
        description="Holistic fit considering role requirements"
    )
    decision: Literal["advance", "reject", "review_with_team"] = Field(
        description="Screening decision based on scores"
    )
```

---

## Routing Pattern

Forces the model to classify into one branch, then fill only that branch's fields. Uses discriminated unions — each variant has a unique `Literal` field.

### Basic Routing with Discriminator

```python
from pydantic import BaseModel, Field
from typing import Literal

class BugReport(BaseModel):
    kind: Literal["bug"] = "bug"
    severity: Literal["low", "medium", "high", "critical"]
    steps_to_reproduce: str
    expected_behavior: str
    actual_behavior: str

class FeatureRequest(BaseModel):
    kind: Literal["feature"] = "feature"
    use_case: str
    proposed_solution: str
    priority: Literal["nice_to_have", "important", "critical"]

class Question(BaseModel):
    kind: Literal["question"] = "question"
    topic: str
    context: str

class IssueTriage(BaseModel):
    """Cascade into routing: summarize first, then classify."""
    user_summary: str = Field(
        description="Restate the user's issue in one sentence"
    )
    issue: BugReport | FeatureRequest | Question = Field(
        discriminator="kind"
    )
```

### Tool Routing for Agents

Each tool is a Pydantic model. The agent's structured output routes to exactly one.

```python
class SendEmail(BaseModel):
    tool: Literal["send_email"] = "send_email"
    to: str = Field(description="Recipient email address")
    subject: str
    body: str

class SearchKnowledgeBase(BaseModel):
    tool: Literal["search_kb"] = "search_kb"
    query: str = Field(description="Search query for knowledge base")
    max_results: Annotated[int, Ge(1), Le(20)] = Field(default=5)

class CreateTicket(BaseModel):
    tool: Literal["create_ticket"] = "create_ticket"
    title: str
    description: str
    priority: Literal["low", "medium", "high"]

class AgentAction(BaseModel):
    reasoning: str = Field(description="Why this tool is the right next step")
    action: SendEmail | SearchKnowledgeBase | CreateTicket = Field(
        discriminator="tool"
    )
```

### Routing with Shared Base

When branches share common fields, use a base class.

```python
class BasePayment(BaseModel):
    amount_cents: int = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    reference: str

class CardPayment(BasePayment):
    method: Literal["card"] = "card"
    last_four: str = Field(pattern=r"^\d{4}$")
    network: Literal["visa", "mastercard", "amex"]

class BankTransfer(BasePayment):
    method: Literal["bank_transfer"] = "bank_transfer"
    bank_name: str
    account_suffix: str

class CryptoPayment(BasePayment):
    method: Literal["crypto"] = "crypto"
    wallet_address: str
    chain: Literal["ethereum", "bitcoin", "solana"]

class PaymentRouter(BaseModel):
    payment: CardPayment | BankTransfer | CryptoPayment = Field(
        discriminator="method"
    )
```

---

## Cycle Pattern

Forces the model to produce a bounded number of structured items. Prevents lazy single-item responses and rambling unbounded lists.

### Basic Cycle with Bounds

```python
from annotated_types import MinLen, MaxLen
from typing import Annotated

class ActionItem(BaseModel):
    task: str = Field(description="Specific actionable task")
    owner: str = Field(description="Person or team responsible")
    deadline: str = Field(description="Target completion date")
    priority: Literal["low", "medium", "high"]

class MeetingNotes(BaseModel):
    summary: str  # Cascade: summarize first
    key_decisions: list[str] = Field(
        min_length=1,
        description="Decisions made during the meeting"
    )
    action_items: Annotated[list[ActionItem], MinLen(1), MaxLen(10)]  # Cycle: bounded
    next_meeting_topic: str  # Cascade: conclude
```

### Cycle + Routing: Parallel Tool Dispatch

When an agent needs to execute multiple tools in parallel, combine Cycle (list of actions) with Routing (each action is a union variant).

```python
class FetchURL(BaseModel):
    tool: Literal["fetch_url"] = "fetch_url"
    url: str

class QueryDB(BaseModel):
    tool: Literal["query_db"] = "query_db"
    sql: str

class CallAPI(BaseModel):
    tool: Literal["call_api"] = "call_api"
    endpoint: str
    payload: dict[str, str | int | bool]

class ParallelExecution(BaseModel):
    plan: str = Field(description="What these parallel actions accomplish together")
    actions: Annotated[
        list[FetchURL | QueryDB | CallAPI],
        MinLen(1),
        MaxLen(5),
    ]
```

---

## Combined Patterns

### Full Agent Step (Cascade + Cycle + Routing)

The canonical SGR agent schema. Used in the adaptive planning pattern.

```python
class ReportDone(BaseModel):
    tool: Literal["report_done"] = "report_done"
    success: bool
    summary: str

class NextStep(BaseModel):
    """Complete agent step combining all three patterns."""
    # Cascade: reflect on current state
    current_state: str = Field(
        description="What has been accomplished and what remains"
    )
    # Cycle: plan ahead (1-5 steps)
    remaining_steps: Annotated[list[str], MinLen(1), MaxLen(5)] = Field(
        description="Brief plan for remaining steps"
    )
    # Cascade: check completion
    task_completed: bool = Field(
        description="Whether the overall task is done"
    )
    # Routing: dispatch to one tool
    action: SendEmail | SearchKnowledgeBase | CreateTicket | ReportDone = Field(
        discriminator="tool",
        description="Execute the first remaining step"
    )
```

### Evaluation with Evidence (Cascade + Cycle)

```python
class Evidence(BaseModel):
    source: str = Field(description="Document or section reference")
    quote: str = Field(description="Relevant excerpt")
    relevance: str = Field(description="How this supports the assessment")

class ComplianceEvaluation(BaseModel):
    # Cascade: understand scope
    regulation_scope: str = Field(
        description="Which regulatory requirements apply"
    )
    # Cascade: analyze
    preliminary_assessment: str = Field(
        description="Initial compliance assessment"
    )
    # Cycle: structured evidence
    supporting_evidence: Annotated[list[Evidence], MinLen(1), MaxLen(8)] = Field(
        description="Evidence supporting the assessment"
    )
    # Cascade: conclude
    compliance_status: Literal["compliant", "non_compliant", "partial"]
    # Cascade: verify (post-answer reconsideration)
    verification_notes: str = Field(
        description="Reconsider: are there gaps the assessment missed?"
    )
    confidence: Literal["low", "medium", "high"]
```

---

## Anti-Patterns

### Conclusion Before Analysis

```python
# WRONG: model decides before reasoning
class BadEval(BaseModel):
    recommendation: Literal["hire", "reject"]  # Conclusion first!
    reasoning: str                              # Post-hoc justification

# RIGHT: analysis drives the conclusion
class GoodEval(BaseModel):
    analysis: str                               # Think first
    recommendation: Literal["hire", "reject"]   # Then decide
```

### Unconstrained Lists

```python
# WRONG: model can produce 0 or 100 items
class BadRisks(BaseModel):
    risks: list[str]  # No bounds

# RIGHT: bounded list forces quality over quantity
class GoodRisks(BaseModel):
    risks: Annotated[list[RiskFactor], MinLen(2), MaxLen(5)]
```

### Prompt Instructions for Schema-Expressible Constraints

```python
# WRONG: "Please rate on a scale of 1-10" in the prompt
score: int  # Model might output 0, 15, or -3

# RIGHT: constraint is guaranteed
score: Annotated[int, Ge(1), Le(10)]
```

### Over-Broad Union Without Discriminator

```python
# WRONG: no discriminator — model may produce ambiguous output
action: SendEmail | SearchKB | CreateTicket

# RIGHT: discriminator forces explicit classification
action: SendEmail | SearchKB | CreateTicket = Field(discriminator="tool")
```

### Doing Math in the Schema

```python
# WRONG: relying on LLM arithmetic
class Invoice(BaseModel):
    items: list[LineItem]
    subtotal: float      # LLM will miscalculate
    tax: float           # LLM will miscalculate
    total: float         # LLM will miscalculate

# RIGHT: extract structured data, compute in Python
class Invoice(BaseModel):
    items: list[LineItem]  # Just the data
    # Calculate subtotal, tax, total in Python after extraction
```
