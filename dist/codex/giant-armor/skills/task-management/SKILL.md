---
name: task-management
description: Use when the user asks to track tasks, track tasks progress, plan steps, create a todo list, create a checklist, break work into subtasks, spawn background tasks, or run tasks in parallel, or when working on multi-step tasks.
---

# Task Management & Background-Agent Orchestration

Use native task tools to track work, manage dependencies, and orchestrate background agents.

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

## Tracking Work

Track work as ordered update_plan items. Keep plan items concise,
maintain at most one `in_progress` item, and update statuses as work advances.

There is no background task graph; represent dependencies with ordering and
clear step names instead of inventing unavailable task-management calls.

## Delegated Work

For delegated work, use spawn_agent only when it is available in
the active tool list or can be discovered through the active harness's
permitted discovery mechanism. If no such tool is available, continue in the
current session and do not invent unavailable task or delegation calls.

## Emulating Orchestration Patterns

Use `references/orchestration-patterns.md` as pattern examples: emulate its
task sequences with ordered update_plan items and its delegation
examples with permitted subagent calls only when those calls are actually
available.

## Orchestration Patterns

For detailed orchestration patterns, see **`references/orchestration-patterns.md`**.
