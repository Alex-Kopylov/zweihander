---
name: interview
description: This skill should be used when the user asks to "walk through items", "review items one by one", "go through the list", "interview me on these", "let's address each item", "explore findings", says "/interview", or wants to systematically work through a presented list of items (code review findings, errors, contradictions, action items) ensuring nothing is missed.
allowed-tools: AskUserQuestion, Read, Edit, Write, Bash
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Item-by-Item Interview

Walk through a list of items one by one using AskUserQuestion, ensuring every item gets a deliberate decision.

When harness-specific adaptation is needed, first identify the active assistant
harness. Load exactly one matching metadata-linked harness reference and skip
non-matching harness files. If no harness-specific adaptation is needed, use
this shared Claude Code-baseline workflow as-is.

## Workflow

### 1. Collect Items

Identify all items from the conversation context. Consolidate if scattered. Number sequentially from 1.

### 2. Present Summary

```
**Interview: [N] items to address**
Starting walk-through. Each item will be presented for your decision.
```

### 3. Walk Through Each Item

Present each item one at a time via AskUserQuestion.

#### Item-to-Question Mapping

- `header`: index + optional severity tag — `"#3 HIGH"` or `"#3"`
- `question`: `"[Title]: [Description] — How to address?"`
- `options`: actionable choices, recommended first

#### Previews

When an item involves code or config, use `preview` on options to show what each action produces (proposed fix, alternative implementation, before/after). Skip preview for trivial items.

#### Example

```
AskUserQuestion({
  questions: [{
    question: "Missing null check in parse_config(): Line 42 dereferences config.timeout without None check — How to address?",
    header: "#3 HIGH",
    options: [
      {
        label: "Fix now (Recommended)",
        description: "Add null check with sensible default",
        preview: "def parse_config(path: str) -> Config:\n    config = load_yaml(path)\n    if config is None:\n        return Config(timeout=30)\n    return Config(timeout=config.timeout)"
      },
      {
        label: "Raise error",
        description: "Fail explicitly instead of defaulting",
        preview: "def parse_config(path: str) -> Config:\n    config = load_yaml(path)\n    if config is None:\n        raise ConfigError(f\"Missing: {path}\")\n    return Config(timeout=config.timeout)"
      },
      { label: "Skip", description: "Accept the risk" }
    ],
    multiSelect: false
  }]
})
```

### 4. Track Progress

After each response, acknowledge briefly and state progress:

```
#3 HIGH — Missing null check: **Fix now** (add null check with default)
Progress: 3/10 items addressed
```

### 5. Execute Decisions

Apply agreed actions after each item, or batch if user prefers.

### 6. Summarize

```
**Interview Complete: [N]/[N] items addressed**

| # | Severity | Item | Decision |
|---|----------|------|----------|
| 1 | HIGH | Missing null check | Fix now |
| 2 | MED | Unused import | Fix now |
| 3 | LOW | Naming convention | Skip |
```

## Rules

- Present every item; never skip one silently.
- If the user asks to batch-fix similar items, group them but log each individually.
- If new items are discovered during fixes, append to the queue and inform the user.
