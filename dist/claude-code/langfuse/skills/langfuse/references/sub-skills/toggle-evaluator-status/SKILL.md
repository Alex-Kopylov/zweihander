---
name: toggle-evaluator-status
description: >
  This skill should be used when the user wants to activate, deactivate, pause,
  resume, enable, or disable an LLM-as-a-Judge evaluator in Langfuse. Trigger
  phrases include "activate evaluator", "deactivate evaluator", "pause
  evaluator", "enable evaluator", "disable all evaluators". It handles safety
  checks and supports bulk status changes.
---

# Toggle Evaluator Status

Activate or deactivate LLM-as-a-Judge evaluators by updating the `status`
column in `job_configurations`.

## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred; install `psycopg2-binary` with `uv add psycopg2-binary` if missing) or docker exec psql fallback.

## Step-by-Step Procedure

### 1. Identify the Evaluator(s)

Accept evaluator name(s) or "all" from the user. Fetch current status:

```python
import psycopg2

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# Single evaluator
cur.execute("""
    SELECT jc.id, et.name, et.version, jc.score_name, jc.status,
           jc.time_scope, jc.filter, jc.sampling
    FROM job_configurations jc
    JOIN eval_templates et ON et.id = jc.eval_template_id
    WHERE jc.project_id = %s AND et.name ILIKE %s
    ORDER BY et.version DESC
""", (PROJECT_ID, f"%{search_term}%"))

# Or all evaluators
cur.execute("""
    SELECT jc.id, et.name, et.version, jc.score_name, jc.status,
           jc.time_scope, jc.filter, jc.sampling
    FROM job_configurations jc
    JOIN eval_templates et ON et.id = jc.eval_template_id
    WHERE jc.project_id = %s
    ORDER BY et.name, et.version DESC
""", (PROJECT_ID,))

jobs = cur.fetchall()
```

Display current status:

```
| Evaluator | Version | Score Name | Current Status | Time Scope |
|-----------|---------|------------|----------------|------------|
| factuality | 3 | factuality | INACTIVE | ['NEW'] |
| no_markdown | 1 | no_markdown | ACTIVE | ['NEW'] |
```

### 2. Safety Checks for Activation

If the user wants to activate (INACTIVE → ACTIVE), perform these checks:

**Verify the template exists and is valid:**

```sql
SELECT id, prompt, model, provider, vars, output_schema
FROM eval_templates
WHERE id = (
    SELECT eval_template_id FROM job_configurations WHERE id = %s
)
```

**Warn about `time_scope` containing `EXISTING`:**

If `time_scope` includes `EXISTING`, warn the user:

```
⚠ WARNING: This evaluator's time_scope includes 'EXISTING'.
Activating it will trigger evaluation of ALL existing matching traces —
this is a one-shot backfill that cannot be cancelled.

Are you sure you want to activate with EXISTING scope? (yes/no)
If not, I can update the time_scope to ['NEW'] before activating.
```

**Warn about activation backfill risk:**

```
Note: Activation may evaluate recent traces depending on Langfuse's internal queue behavior and will process new matching traces immediately.
```

### 3. Show Activation/Deactivation Summary

```
## Proposed Status Change

| Evaluator | Current | New | Score Name |
|-----------|---------|-----|------------|
| factuality | INACTIVE | ACTIVE | factuality |

Proceed? (yes/no)
```

Wait for explicit user confirmation.

### 4. Execute Status Change

### Option A: psycopg2 (Preferred)

**Single evaluator:**

```python
cur.execute("""
    UPDATE job_configurations
    SET status = %s, updated_at = NOW()
    WHERE id = %s AND project_id = %s
""", (new_status, job_id, PROJECT_ID))
conn.commit()
```

**Bulk activate/deactivate all:**

```python
cur.execute("""
    UPDATE job_configurations
    SET status = %s, updated_at = NOW()
    WHERE project_id = %s AND status = %s
""", (new_status, PROJECT_ID, current_status))
updated_count = cur.rowcount
conn.commit()
```

### Option B: docker exec psql (Fallback)

```bash
docker exec -i CONTAINER_NAME psql -U USER -d DBNAME -c "
  UPDATE job_configurations
  SET status = 'NEW_STATUS', updated_at = NOW()
  WHERE id = 'JOB_ID' AND project_id = 'PROJECT_ID';
"
```

### 5. Verify and Report

```sql
SELECT jc.id, et.name, jc.status
FROM job_configurations jc
JOIN eval_templates et ON et.id = jc.eval_template_id
WHERE jc.id = %s AND jc.project_id = %s
```

Report the result:

```
## Status Updated

**Evaluator**: <name>
**New status**: ACTIVE
**Score name**: <score_name>

View in Langfuse: {LANGFUSE_HOST}/project/{PROJECT_ID}/settings/llm-as-a-judge
```

For bulk operations:

```
## Bulk Status Update

**Updated**: <count> evaluator(s) set to <status>
**Evaluators**: <list of names>
```

## Error Handling

- **Evaluator not found**: Report and suggest using `list-evaluators`.
- **Already in target status**: Report that the evaluator is already
  ACTIVE/INACTIVE and no change is needed.
- **No job configuration**: Warn that the template has no associated job config
  and offer to create one via `create-evaluator`.
- **User declines**: Abort without changes.
- **DB connection failed**: Attempt docker exec psql fallback before reporting.

## Cleanup

No temporary files are created by this skill.
