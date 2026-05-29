# Orchestration Patterns

Advanced patterns for multi-agent coordination and task dependency management.

## Pattern 1: Explore → Plan → Execute

Sequential pipeline where exploration informs planning before code is written.

```
TaskCreate: "Explore codebase architecture"        → #1
TaskCreate: "Design implementation plan"            → #2, blockedBy: [#1]
TaskCreate: "Implement authentication module"       → #3, blockedBy: [#2]
TaskCreate: "Write tests for authentication"        → #4, blockedBy: [#3]
```

Step 1 uses an `Explore` agent (read-only, fast). Step 2 uses a `Plan` agent. Steps 3-4 use `general-purpose` agents.

### When to Use
- Large features where the approach is unclear
- Unfamiliar codebases requiring discovery first
- Tasks where wrong assumptions lead to significant rework

## Pattern 2: Parallel Background Agents

Launch multiple independent agents simultaneously, then aggregate results.

```
# Launch in parallel (single message, multiple Agent calls):
Agent(description: "Run unit tests",       prompt: "...", run_in_background: true)
Agent(description: "Run linter",           prompt: "...", run_in_background: true)
Agent(description: "Check type safety",    prompt: "...", run_in_background: true)
Agent(description: "Security audit",       prompt: "...", run_in_background: true)

# Continue other work; aggregate results after completion notifications
```

### When to Use
- CI-like validation (tests, lint, types, security)
- Independent research across different areas
- Multiple file transformations with no shared state

## Pattern 3: Research → Implement

Background agent gathers information while main session continues.

```
# Launch research agent in background
Agent(
  description: "Research OAuth2 patterns",
  prompt: "Search the codebase for existing auth patterns, check documentation...",
  run_in_background: true
)

# Continue current work; use research output when it completes
```

### When to Use
- Need web research or deep codebase exploration before coding
- Current work can continue independently of research
- Time-consuming information gathering

## Pattern 4: Fan-Out / Fan-In

Divide a large task into parallel subtasks, then merge results.

```
TaskCreate: "Prepare migration plan"                → #1
TaskCreate: "Migrate user service"                  → #2, blockedBy: [#1]
TaskCreate: "Migrate payment service"               → #3, blockedBy: [#1]
TaskCreate: "Migrate notification service"          → #4, blockedBy: [#1]
TaskCreate: "Integration testing after migration"   → #5, blockedBy: [#2, #3, #4]
```

Tasks #2, #3, #4 run in parallel after #1 completes. Task #5 waits for all three.

### When to Use
- Multiple independent modules need the same transformation
- Integration testing must follow all parallel work
- Clear separation of concerns between subtasks

## Pattern 5: Iterative Refinement

Run a task, validate, and loop until quality criteria are met.

```
TaskCreate: "Generate initial implementation"       → #1
TaskCreate: "Validate implementation"               → #2, blockedBy: [#1]
# If validation fails:
TaskCreate: "Fix issues from validation"            → #3, blockedBy: [#2]
TaskCreate: "Re-validate after fixes"               → #4, blockedBy: [#3]
```

### When to Use
- Code generation requiring quality validation
- Test-driven workflows (write test, implement, verify)
- Any task with measurable acceptance criteria

## Dependency Management Strategies

### Linear Chain
```
#1 → #2 → #3 → #4
```
Each task blocks the next. Simple and predictable.

### Diamond Pattern
```
    #1
   / \
  #2  #3
   \ /
    #4
```
Task #1 unblocks #2 and #3 (parallel). Task #4 waits for both.

### Independent Groups
```
Group A: #1 → #2
Group B: #3 → #4
Final:   #5 (blockedBy: [#2, #4])
```
Two independent chains converge at a final integration task.

## Best Practices for Multi-Agent Work

### Prompt Quality
Provide complete context in agent prompts — agents cannot see the parent conversation:
- Include file paths, function names, and specific requirements
- State the expected output format
- Mention relevant constraints or conventions

### Agent Isolation
Each background agent has its own context window:
- Agents do not share state with each other
- Pass all necessary information through the prompt
- Collect results from TaskOutput after completion

### Error Handling
- If a background agent fails, its output contains the error
- Check TaskOutput before marking dependent tasks as unblocked
- Create follow-up tasks for failed work rather than retrying blindly

### Resource Awareness
- Background agents consume API tokens independently
- Limit concurrent agents to avoid rate limits (3-5 is reasonable)
- Use `haiku` model for simple tasks to reduce cost
- Reserve `opus` for genuinely complex reasoning

### Resuming Agents
To continue work from a previous agent invocation:
```
Agent(
  resume: "<agent-id>",
  prompt: "Continue from where you left off. The auth module is now complete."
)
```
The agent resumes with full previous context preserved.

## Task Metadata for Orchestration

Attach orchestration metadata for richer coordination:

```
TaskUpdate(taskId: "1", metadata: {
  "agent_type": "Explore",
  "model": "haiku",
  "priority": "critical",
  "estimated_duration": "2m",
  "files": ["src/auth/", "tests/auth/"]
})
```

Useful metadata fields:
- `agent_type` — which agent type to use
- `model` — model override for the agent
- `priority` — critical, high, medium, low
- `estimated_duration` — rough time estimate
- `files` — relevant file paths
- `started_at` / `completed_at` — ISO 8601 timestamps
- `related_issue` — link to GitHub issue
- `test_results` — pass/fail summary
