# SGR Adaptive Planning

## Table of Contents

1. [The Core Idea](#the-core-idea)
2. [The NextStep Schema](#the-nextstep-schema)
3. [Tool Definitions](#tool-definitions)
4. [The Agent Loop](#the-agent-loop)
5. [Conversation Context Management](#conversation-context-management)
6. [Why Constant Replanning Works](#why-constant-replanning-works)
7. [Complete Working Example](#complete-working-example)

---

## The Core Idea

Traditional planning: create a plan upfront, execute it step by step, fail when reality diverges from the plan.

SGR adaptive planning: **regenerate the entire plan at every step.** The model reflects on the current state, plans 1-5 steps ahead, executes only the first step, then replans with the new information. Stale plans are never kept.

This works because planning is cheap for LLMs — a fixed-cost operation regardless of how many times you do it. For humans, replanning is expensive (meetings, documents, coordination). For models, it's just another structured output call.

---

## The NextStep Schema

The heart of adaptive planning. Combines all three SGR patterns:

```python
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from annotated_types import MinLen, MaxLen

class NextStep(BaseModel):
    # Cascade: reflect on what has happened
    current_state: str = Field(
        description="What has been accomplished so far and what context we have"
    )
    # Cycle: plan ahead (bounded)
    plan_remaining_steps_brief: Annotated[list[str], MinLen(1), MaxLen(5)] = Field(
        description="Brief plan for remaining steps to complete the task"
    )
    # Cascade: check if done
    task_completed: bool = Field(
        description="Is the overall task fully complete?"
    )
    # Routing: dispatch to one tool
    function: SendEmail | GetCustomerData | IssueInvoice | VoidInvoice | CreateRule | ReportTaskCompletion = Field(
        description="Execute the first remaining step",
        discriminator="tool",
    )
```

**How it works at each step:**

1. `current_state` — model summarizes what it knows (forces reflection)
2. `plan_remaining_steps_brief` — model plans 1-5 steps (forces lookahead, creates coherence)
3. `task_completed` — model checks if done (prevents premature termination)
4. `function` — model routes to exactly one tool (executes the first planned step)

After execution, the tool result is appended to the conversation, and the model generates a **fresh** NextStep. The plan from step 2 is discarded — only the first action matters.

---

## Tool Definitions

Each tool is a Pydantic model with a `Literal` discriminator. Keep business constraints in the schema, not the prompt.

```python
class SendEmail(BaseModel):
    tool: Literal["send_email"] = "send_email"
    to: str = Field(description="Recipient email address")
    subject: str
    body: str
    attachments: list[str] = Field(default_factory=list)

class GetCustomerData(BaseModel):
    tool: Literal["get_customer_data"] = "get_customer_data"
    email: str = Field(description="Customer email to look up")

class IssueInvoice(BaseModel):
    tool: Literal["issue_invoice"] = "issue_invoice"
    customer_email: str
    items: list[dict[str, str | int]]  # [{"sku": "...", "qty": 1}]
    discount_percent: Annotated[int, Ge(0), Le(50)] = Field(
        default=0,
        description="Discount percentage (max 50%)"
    )

class VoidInvoice(BaseModel):
    tool: Literal["void_invoice"] = "void_invoice"
    invoice_id: str
    reason: str

class CreateRule(BaseModel):
    tool: Literal["create_rule"] = "create_rule"
    customer_email: str
    rule_description: str = Field(
        description="Persistent rule to remember for this customer"
    )

class ReportTaskCompletion(BaseModel):
    tool: Literal["report_done"] = "report_done"
    success: bool
    summary: str = Field(description="Brief summary of what was accomplished")
```

**Note:** `discount_percent: Annotated[int, Ge(0), Le(50)]` guarantees the max discount at the schema level. No prompt instruction needed — constrained decoding enforces it.

---

## The Agent Loop

The loop is simple. Each iteration: parse structured output, check for completion, dispatch the tool, append results to context.

```python
from openai import OpenAI

def run_agent(
    client: OpenAI,
    system_prompt: str,
    task: str,
    max_steps: int = 20,
) -> str:
    """Run an SGR adaptive planning agent loop."""
    log: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    for step in range(max_steps):
        # Get structured next step
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=log,
            response_format=NextStep,
        )
        next_step = response.choices[0].message.parsed

        # Check for completion
        if isinstance(next_step.function, ReportTaskCompletion):
            return next_step.function.summary

        # Execute the tool
        tool_result = dispatch(next_step.function)

        # Append to conversation context
        log.append({
            "role": "assistant",
            "content": f"State: {next_step.current_state}\n"
                       f"Plan: {next_step.plan_remaining_steps_brief}\n"
                       f"Action: {next_step.function.model_dump_json()}",
        })
        log.append({
            "role": "user",  # Tool results go as user messages
            "content": f"Tool result: {tool_result}",
        })

    return "Max steps reached without completion"
```

### Dispatch Function

Route to the right handler via `isinstance`. Keep math and validation in Python.

```python
def dispatch(action: BaseModel) -> str:
    """Execute a tool action and return the result as a string."""
    match action:
        case SendEmail():
            # Simulate sending email
            return f"Email sent to {action.to}: {action.subject}"

        case GetCustomerData():
            data = db.get_customer(email=action.email)
            if data is None:
                return f"No customer found with email {action.email}"
            return json.dumps(data, indent=2)

        case IssueInvoice():
            # Compute totals in Python — never trust LLM arithmetic
            items = resolve_items(action.items)
            subtotal = sum(item["price"] * item["qty"] for item in items)
            discount = subtotal * action.discount_percent / 100
            total = subtotal - discount
            invoice_id = create_invoice(
                customer_email=action.customer_email,
                items=items,
                total_cents=int(total * 100),
            )
            return f"Invoice {invoice_id} created. Total: ${total:.2f}"

        case VoidInvoice():
            void_invoice(invoice_id=action.invoice_id, reason=action.reason)
            return f"Invoice {action.invoice_id} voided: {action.reason}"

        case CreateRule():
            save_rule(email=action.customer_email, rule=action.rule_description)
            return f"Rule saved for {action.customer_email}"

        case _:
            return f"Unknown action type: {type(action).__name__}"
```

---

## Conversation Context Management

The growing conversation log IS the agent's memory within a task. Each step adds:
1. The assistant's reasoning (state + plan + action)
2. The tool result

This means:
- **The model sees all prior actions and results** when planning the next step
- **New information is immediately available** — if a tool returns unexpected data, the next plan incorporates it
- **No separate memory system needed** within a single task

For multi-task agents, you might add a rules/memory system (like the `CreateRule` tool above) that persists across tasks.

---

## Why Constant Replanning Works

**The SkyNet example:** An agent receives a task to sell products to a customer. A restriction rule against that customer was stored in a previous session. The agent doesn't know about the rule initially — only after calling `GetCustomerData` does it discover the restriction. In a traditional plan-then-execute system, this would require plan recovery logic. With adaptive planning, the next `NextStep` naturally incorporates the restriction because the plan is regenerated from scratch with full context.

**Cost model:** Each `NextStep` generation costs the same regardless of plan complexity. The model doesn't carry forward stale assumptions — every step is a fresh assessment of the full conversation context.

**When replanning is insufficient:** If a task requires more than ~20 steps, the conversation context grows large and the model may lose coherence. For very long tasks, consider breaking them into subtasks with separate agent loops.

---

## Complete Working Example

A minimal but functional agent (~100 lines) that handles customer service tasks.

```python
import json
from typing import Annotated, Literal

from annotated_types import Ge, Le, MinLen, MaxLen
from openai import OpenAI
from pydantic import BaseModel, Field


# --- Tool schemas ---

class SendEmail(BaseModel):
    tool: Literal["send_email"] = "send_email"
    to: str
    subject: str
    body: str

class GetCustomerData(BaseModel):
    tool: Literal["get_customer"] = "get_customer"
    email: str

class IssueInvoice(BaseModel):
    tool: Literal["issue_invoice"] = "issue_invoice"
    customer_email: str
    items: list[dict[str, str | int]]
    discount_percent: Annotated[int, Ge(0), Le(50)] = 0

class ReportDone(BaseModel):
    tool: Literal["done"] = "done"
    success: bool
    summary: str


# --- NextStep schema ---

class NextStep(BaseModel):
    current_state: str
    plan: Annotated[list[str], MinLen(1), MaxLen(5)]
    task_completed: bool
    action: SendEmail | GetCustomerData | IssueInvoice | ReportDone = Field(
        discriminator="tool"
    )


# --- In-memory database ---

DB: dict[str, dict] = {
    "customers": {
        "alice@example.com": {"name": "Alice", "discount": 10},
    },
    "invoices": {},
}


# --- Dispatch ---

def dispatch(action: BaseModel) -> str:
    match action:
        case SendEmail():
            return f"Email sent to {action.to}"
        case GetCustomerData():
            data = DB["customers"].get(action.email)
            return json.dumps(data) if data else "Customer not found"
        case IssueInvoice():
            inv_id = f"INV-{len(DB['invoices']) + 1}"
            DB["invoices"][inv_id] = action.model_dump()
            return f"Invoice {inv_id} created"
        case _:
            return "Unknown action"


# --- Agent loop ---

def run(task: str) -> str:
    client = OpenAI()
    system = "You are a helpful business assistant. Use tools to complete tasks."

    log = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]

    for _ in range(20):
        resp = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=log,
            response_format=NextStep,
        )
        step = resp.choices[0].message.parsed

        if isinstance(step.action, ReportDone):
            return step.action.summary

        result = dispatch(step.action)

        log.append({"role": "assistant", "content": step.model_dump_json()})
        log.append({"role": "user", "content": f"Result: {result}"})

    return "Max steps reached"


if __name__ == "__main__":
    print(run("Look up alice@example.com and send her an invoice for 2x Widget at $50 each"))
```

**What this demonstrates:**
- All three patterns in action (Cascade + Cycle + Routing)
- Schema-enforced discount cap (max 50%)
- No math in the LLM — invoice calculations happen in `dispatch`
- Adaptive replanning — the agent discovers Alice's 10% discount via `GetCustomerData` and applies it in the next step
- Growing conversation context as implicit memory
