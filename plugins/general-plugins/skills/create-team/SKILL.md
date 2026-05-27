---
name: create-team
description: Use when the user wants to design a multi-agent team with clear roles, dependencies, handoffs, and review steps.
metadata:
  ai-harness-codex: reference/codex.md
  ai-harness-claude-code: reference/claude-code.md
---

# Create Team

Design a multi-agent team blueprint with clear role separation and interaction patterns. If harness-specific tool mapping is needed, load exactly one matching reference from `metadata.ai-harness-*`. If no exact AI harness match exists, do not load a harness reference.

## Process

### Phase 1: Understand the Mission

Read the user's input and identify what they want the team to accomplish. If the goal is unclear or too broad, ask concise clarifying questions:

- What is the end goal or deliverable?
- What is the scope and complexity?
- Are there constraints?

### Phase 2: Deep-Dive Interview

Gather specifics. Do NOT skip this phase - ask at least 2-3 rounds of questions covering:

- **Work decomposition**: What are the major workstreams? Can they run in parallel or must they be sequential?
- **Risk areas**: Where are the tricky parts? What needs the most careful review?
- **Communication needs**: Do agents need to share intermediate results? Are there handoff points?

### Phase 3: Design the Team

Based on gathered requirements, design the team with:

1. **Team name** - short, descriptive kebab-case name
2. **Team purpose** - one-sentence mission statement
3. **Roles** - for each team member define:
   - **Name** (kebab-case, e.g., `backend-dev`, `test-engineer`)
   - **Role mode** (implementation, read-only research, planning/design, review/QA)
   - **Responsibility** - clear, bounded scope of what this agent owns
   - **Inputs** - what does this agent need from others before starting?
   - **Outputs** - what does this agent produce for others?
4. **Interaction map** - who communicates with whom:
   - Direct dependencies (agent A blocks agent B)
   - Review relationships (agent A reviews agent B's work)
   - Information flows (agent A shares findings with agent B)
5. **Task sequence** - ordered list of tasks with:
   - Owner (which agent)
   - Dependencies (blocked by which tasks)
   - Description of the work
6. **Model tier** - ask what capability level each role should use
   - Highest-capability reasoning model - complex, multi-step work with lots of dependencies
   - Balanced model - straightforward implementation work with modest dependencies
   - Fast model - direct short tasks with no dependencies

### Phase 4: Present the Blueprint

Present the full team design to the user as a structured document. Include:

- A visual-style interaction diagram using text/ASCII showing communication flows
- A task dependency graph
- Clear explanation of why each role exists and how they interact

### Phase 5: Write the Blueprint

After user approval, write the team blueprint to the appropriate task, plan, or project location for the active AI harness.

## Task And Agent Tools

Track progress with the active harness's task or plan mechanism. Spawn parallel agents only when the active harness supports it and the team design justifies the coordination overhead.

## Rules

- Always include a review/QA step for non-trivial teams. Prefer TDD-style implementation where applies.
- Design for minimal communication overhead - agents that don't need to talk shouldn't.
