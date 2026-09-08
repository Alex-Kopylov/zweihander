---
name: interview
description: This skill should be used when the user asks to "walk through items", "review items one by one", "go through the list", "interview me on these", "let's address each item", "explore findings", says "/interview", or wants to systematically work through a presented list of items (code review findings, errors, contradictions, action items) ensuring nothing is missed.
metadata:
  argument-hint: "[items] — list, file, or PR to walk through; defaults to the most recent list in this conversation"
  arguments: items
  config:
    decision-log-dir: "${TMPDIR:-/tmp}/interview-decision-logs"
---

# Item-by-Item Interview

Walk through a list of items one by one by asking the user one bounded question per item, ensuring every item gets a deliberate decision. Nothing is executed until the user approves the decision log.

## Workflow

### 1. Collect Items

Collect the items the invocation argument names. When the invocation carries no argument, collect the items from the conversation context.

Consolidate if scattered. Number sequentially from 1.

### 2. Group Questions

Two items belong to one group when a single answer resolves both: the same root cause, the same convention, or the same repository-wide rule.

When at least one group exists, ask once via $request_user_input, before any item question:

- `question`: `"Some items share one decision. Which groups do you want to answer once?"`
- `options`: one per group — label the shared decision, list the item indexes in the description
- `multiSelect`: true

A selected group becomes one question in step 4. An unselected group splits back into one question per item. Skip this step when no two items share a decision.

### 3. Open the Decision Log

Run once, with the item total and a short name for this interview:

```
scripts/decision_log.py start --total [N] --name "[short-name]"
```

Keep the printed path. Every later call takes it back as `--log`. Then present:

```
**Interview: [N] items in [K] questions**
Decision log: [path]
▱▱▱▱▱▱▱▱▱▱  0/[N]
```

### 4. Walk Through Each Question

Present each question one at a time as a bounded user question via $request_user_input.

#### Item-to-Question Mapping

- `header`: index + optional severity tag — `"#3 HIGH"` or `"#3"`; for a group, the indexes — `"#2 #5 #7"`
- `question`: `"[Title]: [Description] — How to address?"`
- `options`: actionable choices, recommended first

#### Previews

When an item involves code or config, use `preview` on options to show what each action produces (proposed fix, alternative implementation, before/after). Skip preview for trivial items.
When the input mechanism does not support preview fields, present proposed
code/config previews in chat before the question, or fold brief previews into
the option description.

#### Example

```
Question: "Missing null check in parse_config(): Line 42 dereferences config.timeout without None check — How to address?"
Header: "#3 HIGH"
Options:
- Label: "Fix now (Recommended)"
  Description: "Add null check with sensible default"
  Preview: "def parse_config(path: str) -> Config:\n    config = load_yaml(path)\n    if config is None:\n        return Config(timeout=30)\n    return Config(timeout=config.timeout)"
- Label: "Raise error"
  Description: "Fail explicitly instead of defaulting"
  Preview: "def parse_config(path: str) -> Config:\n    config = load_yaml(path)\n    if config is None:\n        raise ConfigError(f\"Missing: {path}\")\n    return Config(timeout=config.timeout)"
- Label: "Skip"
  Description: "Accept the risk"
Multi-select: false
```

### 5. Record Each Decision

Record the answer before asking the next question:

```
scripts/decision_log.py record --log "[path]" --decision "[decision]" --item "[#3 HIGH — Missing null check]"
```

Repeat `--item` once per item when one answer covers a group. Show the script output as it comes back — its last line is the progress bar:

```
#3 HIGH — Missing null check: **Fix now** (add null check with default)
▰▰▰▱▱▱▱▱▱▱  3/10
```

Never count addressed items yourself; the log holds the count. When new items appear, run `scripts/decision_log.py extend --log "[path]" --by [n]`, then add them to the queue and tell the user.

### 6. Review the Decision Log

Nothing has been executed yet. Print the whole log:

```
scripts/decision_log.py show --log "[path]"
```

Then ask via $request_user_input whether to execute it, amend a decision, or stop. Amending re-asks that item's question and records the new answer.

### 7. Execute Decisions

Apply the agreed actions only after the user approves the log. Report each failure against the log row it belongs to.

## Delegation

The interview stays responsive, so work that does not need the user runs beside it via $spawn_agent:

- **Previews** — while the user answers one question, a background agent drafts the previews for the questions ahead.
- **Log prose** — the short name in step 3 and the closing summary in step 6 go to a writer agent on the smallest, cheapest model the harness offers.
- **Execution** — in step 7, independent decisions fan out one agent each, per $dev-workflow:dispatching-parallel-agents. Decisions that touch one file stay in one agent, in order.

Recording a decision is a script call, never an agent call: a round trip per answer would stall the walk-through.

## Rules

- Present every item; never skip one silently.
- Group items in step 2 only, and log each item on its own row.
- Execute nothing before the user approves the log in step 6.
