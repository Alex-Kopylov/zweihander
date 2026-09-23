# Orchestration Patterns

Advanced patterns for multi-agent coordination and task dependency management.

## Pattern 1: Explore → Plan → Execute

Use a sequential pipeline when exploration must inform the plan before
implementation starts.


```
TaskCreate: "Explore codebase architecture"        → #1
TaskCreate: "Design implementation plan"            → #2, blockedBy: [#1]
TaskCreate: "Implement authentication module"       → #3, blockedBy: [#2]
TaskCreate: "Write tests for authentication"        → #4, blockedBy: [#3]
```

Step 1 uses an `Explore` agent. Step 2 uses a `Plan` agent. Steps 3
and 4 use `general-purpose` agents.


### When to Use

- The approach is unclear
- The codebase is unfamiliar
- Wrong assumptions can cause significant rework

## Pattern 2: Parallel Agents

Launch independent agents together. Continue non-overlapping work, then
aggregate their results.


```
Agent(description: "Run unit tests", prompt: "...", run_in_background: true)
Agent(description: "Run linter", prompt: "...", run_in_background: true)
Agent(description: "Check type safety", prompt: "...", run_in_background: true)
Agent(description: "Run security audit", prompt: "...", run_in_background: true)
```


Wait only when the next step requires an agent result.

### When to Use

- Two or more tasks are independent
- Each agent has a distinct read or write scope
- Parallel work reduces the critical path

## Pattern 3: Research → Implement

Let one agent gather information while the main session continues independent
work.


```
Agent(
  description: "Research OAuth2 patterns",
  prompt: "Find existing authentication patterns and return file paths.",
  run_in_background: true
)
```


Do not repeat the delegated research in the main session. Integrate the result
after the agent reports completion.

### When to Use

- The research has a concrete output
- Current work can continue without the result
- The research does not duplicate main-session work

## Pattern 4: Fan-Out / Fan-In

Divide a large task into independent branches. Integrate only after every
required branch finishes.


```
TaskCreate: "Prepare migration plan"                → #1
TaskCreate: "Migrate user service"                  → #2, blockedBy: [#1]
TaskCreate: "Migrate payment service"               → #3, blockedBy: [#1]
TaskCreate: "Migrate notification service"          → #4, blockedBy: [#1]
TaskCreate: "Run integration tests"                 → #5, blockedBy: [#2, #3, #4]
```


Start integration only after all required results are available.

### When to Use

- Multiple modules have disjoint scopes
- The same transformation applies to each module
- A final step depends on every branch

## Pattern 5: Iterative Refinement

Run one iteration, validate it, and repeat until the acceptance criteria pass.


```
TaskCreate: "Generate initial implementation"       → #1
TaskCreate: "Validate implementation"               → #2, blockedBy: [#1]
TaskCreate: "Fix validation findings"               → #3, blockedBy: [#2]
TaskCreate: "Re-run validation"                     → #4, blockedBy: [#3]
```


Add or revise a step when validation changes the required work.

### When to Use

- Code generation requires validation
- The workflow uses test-driven development
- The task has measurable acceptance criteria

## Dependency Management

Use a linear order for sequential work. For fan-out and fan-in, start the
independent branches together and wait before integration.


Represent explicit relationships with task dependencies.

```
Linear:  #1 → #2 → #3
Fan-out: #1 → [#2, #3] → #4
```


## Best Practices for Multi-Agent Work

### Task Quality

- Keep tasks short and outcome-focused
- Mark work complete only after validation
- State file paths, constraints, and the expected result



### Delegated Context

Do not rely on inherited context. Give each agent the information required to
complete its task and return a useful result.

### Error Handling

- Check an agent result before starting dependent work
- Keep a blocked step open until the blocker is resolved
- Send follow-up work to an existing agent when its context remains useful

### Resource Awareness

- Each agent consumes tokens independently
- Use only the concurrency that the current session exposes
- Keep concurrent write scopes disjoint


- Use `haiku` for simple searches
- Reserve `opus` for complex reasoning


### Follow-Up Work


```
Agent(
  resume: "<agent-id>",
  prompt: "Continue from where you stopped. The dependency is now ready."
)
```


### Task Details


Attach task metadata when the extra fields improve coordination.

```
TaskUpdate(taskId: "1", metadata: {
  "priority": "critical",
  "files": ["src/auth/", "tests/auth/"],
  "estimated_duration": "2m"
})
```
