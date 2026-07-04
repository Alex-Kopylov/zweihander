---
name: delete-evaluator
description: >
  Use when the user wants to delete or remove an LLM-as-a-Judge evaluator from
  Langfuse. Trigger phrases: "delete evaluator", "remove evaluator", "drop
  evaluator", "clean up evaluator". Handles safety checks, confirmation,
  transaction-wrapped deletion of job_configurations and eval_templates, and
  post-deletion verification.
---

# Delete LLM-as-a-Judge Evaluator



## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- `psycopg2-binary`; if missing, install via `uv add psycopg2-binary`.

---

## Step-by-Step Procedure

### 1. Identify the Evaluator

Accept the evaluator name or ID from the user. Fetch template versions and job
configurations:

```python
import psycopg2
import json

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# All template versions
cur.execute("""
    SELECT id, name, version, model, provider, created_at
    FROM eval_templates
    WHERE project_id = %s AND name ILIKE %s
    ORDER BY version DESC
""", (PROJECT_ID, f"%{search_term}%"))
templates = cur.fetchall()

# All job configurations for this evaluator
cur.execute("""
    SELECT jc.id, jc.eval_template_id, et.version,
           jc.score_name, jc.status, jc.created_at
    FROM job_configurations jc
    JOIN eval_templates et ON et.id = jc.eval_template_id
    WHERE jc.project_id = %s AND et.name = %s
    ORDER BY et.version DESC
""", (PROJECT_ID, evaluator_name))
jobs = cur.fetchall()
```

### 2. Show Current State

Present all versions and job configurations:

```
## Evaluator: <name>

### Template Versions
| Version | Template ID | Model | Created |
|---------|-------------|-------|---------|
| 3 | cmm66... | gpt-4o | 2024-12-15 |
| 2 | cmm55... | gpt-4o | 2024-12-10 |
| 1 | cmm44... | gpt-3.5-turbo | 2024-12-01 |

### Job Configurations
| Job ID | Template Version | Score Name | Status | Created |
|--------|-----------------|------------|--------|---------|
| cmm77... | 3 | factuality | ACTIVE | 2024-12-15 |
| cmm88... | 2 | factuality | INACTIVE | 2024-12-10 |
```

### 3. Warn About Active Job Configurations

If any job configuration has `status = 'ACTIVE'`:

```
⚠ WARNING: This evaluator has ACTIVE job configurations:
  - Job cmm77... (v3) — score: factuality — ACTIVE

Deleting will stop all active evaluations immediately.
```

### 4. Present Deletion Options

Offer two options:

```
**Option A: Delete job configuration(s) only**
  Removes job configurations but preserves template versions for future reuse.

**Option B: Full cleanup**
  Removes ALL job configurations AND all template versions.

Historical scores in the scores table are NOT affected.

Which option? (A/B)
```

### 5. Require Explicit Confirmation

After option selection, require final confirmation:

```
This will permanently delete:
  <Option A>: <N> job configuration(s)
  <Option B>: <N> job configuration(s) + <M> template version(s)

Type "confirm" to proceed.
```

### 6. Execute Deletion

Wrap the deletion in a transaction:

### Option A: psycopg2 (Preferred)

```python
conn.autocommit = False
try:
    with conn.cursor() as cur:
        if option == "A":
            cur.execute("""
                DELETE FROM job_configurations
                WHERE project_id = %s
                  AND eval_template_id IN (
                      SELECT id FROM eval_templates
                      WHERE project_id = %s AND name = %s
                  )
            """, (PROJECT_ID, PROJECT_ID, evaluator_name))
            deleted_jobs = cur.rowcount

        elif option == "B":
            # Delete job configurations first (FK dependency)
            cur.execute("""
                DELETE FROM job_configurations
                WHERE project_id = %s
                  AND eval_template_id IN (
                      SELECT id FROM eval_templates
                      WHERE project_id = %s AND name = %s
                  )
            """, (PROJECT_ID, PROJECT_ID, evaluator_name))
            deleted_jobs = cur.rowcount

            # Then delete all template versions
            cur.execute("""
                DELETE FROM eval_templates
                WHERE project_id = %s AND name = %s
            """, (PROJECT_ID, evaluator_name))
            deleted_templates = cur.rowcount

    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

### Option B: docker exec psql (Fallback)

```bash
docker exec -i CONTAINER_NAME psql -U USER -d DBNAME -c "
  BEGIN;

  DELETE FROM job_configurations
  WHERE project_id = 'PROJECT_ID'
    AND eval_template_id IN (
        SELECT id FROM eval_templates
        WHERE project_id = 'PROJECT_ID' AND name = 'EVALUATOR_NAME'
    );

  -- For full cleanup only:
  DELETE FROM eval_templates
  WHERE project_id = 'PROJECT_ID' AND name = 'EVALUATOR_NAME';

  COMMIT;
"
```

### 7. Verify Deletion

Confirm the records are gone:

```sql
-- Verify job configs deleted
SELECT COUNT(*) FROM job_configurations
WHERE project_id = %s
  AND eval_template_id IN (
      SELECT id FROM eval_templates
      WHERE project_id = %s AND name = %s
  );

-- Verify templates deleted (Option B only)
SELECT COUNT(*) FROM eval_templates
WHERE project_id = %s AND name = %s;
```

### 8. Report Summary

```
## Deletion Complete

**Evaluator**: <name>
**Job configurations deleted**: <count>
**Template versions deleted**: <count> (or "preserved" for Option A)

Note: Historical scores produced by this evaluator remain in the `scores` table
and are not affected by this deletion.
```

---

## Error Handling

- **Evaluator not found**: Report and suggest using `list-evaluators`.
- **User declines confirmation**: Abort the operation entirely.
- **Transaction failure**: Roll back and report the error; no partial deletions should remain.
- **DB connection failed**: Attempt docker exec psql fallback before reporting.

---

## Cleanup

No temporary files are created by this skill.
