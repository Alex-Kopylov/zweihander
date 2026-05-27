---
name: task-management
description: This skill should be used when the user asks to "track tasks", "create a todo list", "manage background tasks", "use TaskCreate", "orchestrate agents", "run tasks in parallel", "break this into tasks", "track progress", "create a checklist", "plan steps", "divide work into subtasks", or when working on multi-step tasks. Also activates when the user mentions TaskCreate, TaskGet, TaskList, TaskUpdate, TaskOutput, or TaskStop.
---

# Task Management & Background Agent Orchestration

Guide for using native task tools (TaskCreate, TaskGet, TaskList, TaskUpdate, TaskOutput, TaskStop) to track work, manage dependencies, and orchestrate background agents.

## When to Use Task Tools

Create a task list when:
- A task requires **3 or more distinct steps**
- Work involves **parallel sub-agents** or background operations
- The user explicitly requests task tracking
- A plan or checklist needs structured progress tracking

Skip task tools when:
- There is a single, trivial task
- The task completes in fewer than 3 simple steps
- The interaction is purely conversational

## Core Tools Quick Reference

| Tool | Purpose | Key Fields |
|------|---------|------------|
| **TaskCreate** | Create a task | `subject` (imperative), `description`, `activeForm` (spinner text) |
| **TaskGet** | Fetch full task details | `taskId` — returns description, metadata, dependencies |
| **TaskList** | List all tasks (summary only) | Returns id, subject, status, owner, blockedBy |
| **TaskUpdate** | Update status or dependencies | `taskId`, `status`, `addBlockedBy`, `addBlocks`, `owner`, `metadata` |
| **TaskOutput** | Read output from background task | `task_id`, `block` (true/false), `timeout` |
| **TaskStop** | Stop a running background task | `task_id` |

> **Note:** TaskCreate/Get/List/Update use `taskId` (camelCase). TaskOutput and TaskStop use `task_id` (snake_case).

## Task Lifecycle

Status flows in one direction:

```
pending → in_progress → completed
```

- Set `in_progress` **before** starting work on a task
- Set `completed` **only after** work is fully done and validated
- Use `deleted` to permanently remove a task that is no longer needed
- There is no `failed` status — if blocked, keep as `in_progress` and create a new task describing the blocker

## Creating Effective Tasks

### Subject Line

Write in **imperative form** — a brief, actionable title:
- "Add authentication middleware"
- "Fix decimal rounding in payments"
- "Run integration test suite"

### ActiveForm

Present continuous form displayed in the spinner while `in_progress`:
- "Adding authentication middleware"
- "Fixing decimal rounding"
- "Running integration tests"

### Description

Keep descriptions concise (50-100 words). Include:
- What needs to be done
- Acceptance criteria
- Context another agent would need

For large plans, reference external files instead of inline descriptions:
```
See docs/plan-auth.md for full implementation details
```

## Dependency Management

Chain tasks using `addBlockedBy` and `addBlocks`:

```
TaskCreate: "Write unit tests"         → task #1
TaskCreate: "Run test suite"           → task #2
TaskUpdate: taskId #2, addBlockedBy: ["1"]
```

Task #2 cannot start until task #1 is completed. After completing task #1, check TaskList to find newly unblocked tasks.

## Background Agent Orchestration

Launch agents in the background using the **Agent tool** with `run_in_background: true`:

```
Agent(
  description: "Run linting checks",
  prompt: "Run ruff check on the src/ directory and report results",
  run_in_background: true
)
```

After launching, continue other work. A notification arrives when the agent completes. To manually check:

```
TaskOutput(task_id: "<agent-id>", block: false, timeout: 5000)
```

To stop a background agent that is no longer needed:

```
TaskStop(task_id: "<agent-id>")
```

### Parallel Agent Pattern

Launch multiple independent agents simultaneously for maximum throughput:

```
# In a single message, launch all independent agents:
Agent(description: "Run tests",     prompt: "...", run_in_background: true)
Agent(description: "Lint codebase", prompt: "...", run_in_background: true)
Agent(description: "Check types",   prompt: "...", run_in_background: true)
```

Each agent runs in its own context window, consuming no parent context budget.

### Agent Type Selection

| Need | Agent Type |
|------|-----------|
| Read-only codebase search | `Explore` |
| Implementation strategy | `Plan` |
| Multi-step coding or research | `general-purpose` |
| Specific domain task | Named subagent (e.g., `test-runner`) |

Match model to complexity:
- `haiku` — simple searches, repetitive tasks
- `sonnet` — code generation, complex tasks (default)
- `opus` — critical decisions, complex reasoning

## TaskList Limitation

**TaskList returns summary fields only**: id, subject, status, owner, blockedBy.

To access `description`, `metadata`, or `activeForm`, make an explicit `TaskGet(taskId)` call. This is by design to prevent context bloat — 20 tasks in TaskList costs 1 call, but full details would cost 21 calls.

**Mitigation**: Embed critical info in the `subject` field (always visible in TaskList) and keep descriptions concise.

## Metadata Conventions

Attach structured metadata to tasks for richer tracking:

```
TaskUpdate(taskId: "1", metadata: {
  "priority": "high",
  "files": ["src/auth.ts", "tests/auth.test.ts"],
  "estimated_duration": "30m"
})
```

Set a metadata key to `null` to remove it.

## Common Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Marking complete without validation | Run tests/checks first, then set `completed` |
| Assuming description visible in TaskList | Use TaskGet per task when details needed |
| Deeply nested task hierarchies | Flatten — use blockedBy for sequencing |
| Huge inline descriptions | Reference external plan files |
| Blocking main session for slow agents | Use `run_in_background: true` |
| Polling background tasks in a loop | Wait for notification, or use TaskOutput with `block: true` |

## Orchestration Patterns

For detailed orchestration patterns (explore-plan-execute, research-implement, parallel validation), consult:

- **`references/orchestration-patterns.md`** — Multi-agent coordination patterns, workflow templates, and advanced dependency management strategies
