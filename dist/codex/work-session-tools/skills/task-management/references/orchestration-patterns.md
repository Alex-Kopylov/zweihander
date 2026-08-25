# Orchestration Patterns

Advanced patterns for multi-agent coordination and task dependency management.

## Pattern 1: Explore → Plan → Execute

Use a sequential pipeline when exploration must inform the plan before
implementation starts.


```
update_plan(plan: [
  {step: "Explore codebase architecture", status: "in_progress"},
  {step: "Design implementation plan", status: "pending"},
  {step: "Implement authentication module", status: "pending"},
  {step: "Write tests for authentication", status: "pending"}
])
```

Send the complete ordered plan on each update. Keep at most one item
`in_progress`.


### When to Use

- The approach is unclear
- The codebase is unfamiliar
- Wrong assumptions can cause significant rework

## Pattern 2: Parallel Agents

Launch independent agents together. Continue non-overlapping work, then
aggregate their results.


Delegate only when the user or applicable project instructions authorize it.

```
spawn_agent(
  task_name: "run_unit_tests",
  message: "Run the unit tests. Return each failure with its file path."
)
spawn_agent(
  task_name: "check_types",
  message: "Run the type checker. Return each error with its file path."
)
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
spawn_agent(
  task_name: "research_oauth",
  message: "Find existing authentication patterns and return file paths."
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
update_plan(plan: [
  {step: "Prepare the migration plan", status: "completed"},
  {step: "Migrate the independent services", status: "in_progress"},
  {step: "Run integration tests", status: "pending"}
])
```

Use one bounded agent task for each independent service when delegation is
authorized.


Start integration only after all required results are available.

### When to Use

- Multiple modules have disjoint scopes
- The same transformation applies to each module
- A final step depends on every branch

## Pattern 5: Iterative Refinement

Run one iteration, validate it, and repeat until the acceptance criteria pass.


```
update_plan(plan: [
  {step: "Generate the initial implementation", status: "completed"},
  {step: "Validate the implementation", status: "completed"},
  {step: "Fix validation findings", status: "in_progress"},
  {step: "Re-run validation", status: "pending"}
])
```


Add or revise a step when validation changes the required work.

### When to Use

- Code generation requires validation
- The workflow uses test-driven development
- The task has measurable acceptance criteria

## Dependency Management

Use a linear order for sequential work. For fan-out and fan-in, start the
independent branches together and wait before integration.


The plan is an ordered checklist, not a dependency graph. Express dependencies
through step order and clear step text. Use agent lifecycle tools only for
delegated work.


## Best Practices for Multi-Agent Work

### Task Quality

- Keep tasks short and outcome-focused
- Mark work complete only after validation
- State file paths, constraints, and the expected result


- Send the complete plan on every update
- Keep at most one plan item `in_progress`


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


- Omit model overrides unless the user or applicable instructions require one


### Follow-Up Work


Use a lifecycle tool exposed in the current session. Continue the existing
agent when its prior context remains relevant.


### Task Details


Plan items accept only the fields exposed by the active tool schema. Put
priority, file paths, and other context in the step text or delegated-agent
message.
