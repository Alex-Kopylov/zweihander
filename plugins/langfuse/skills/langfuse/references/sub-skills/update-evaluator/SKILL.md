---
name: update-evaluator
description: >
  Use when updating an existing Langfuse LLM-as-a-Judge evaluator. Trigger
  phrases include "update evaluator", "modify evaluator", "change evaluator
  prompt", "update evaluation filters", and "change evaluator model". Handles
  template-level changes (new version) and job-config-level changes (in-place
  update).
---

# Update LLM-as-a-Judge Evaluator

Update an existing Langfuse LLM-as-a-Judge evaluator by separating changes into
template-level (new version) and job-config-level (in-place update).

---

## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python libraries `cuid2` and `psycopg2-binary`; install missing packages with
  `uv add cuid2 psycopg2-binary`.

For complete schema details, consult `create-evaluator`'s
`references/evaluator-schema-reference.md`.

---

## Step-by-Step Procedure

### 1. Identify the Evaluator

Accept the evaluator name or ID from the user. Fetch the current configuration
using the same lookup logic as the `inspect-evaluator` skill:

```python
cur.execute("""
    SELECT et.id, et.name, et.version, et.prompt, et.model, et.provider,
           et.model_params, et.vars, et.output_schema,
           jc.id AS job_id, jc.score_name, jc.status, jc.filter,
           jc.variable_mapping, jc.sampling, jc.delay, jc.time_scope
    FROM eval_templates et
    LEFT JOIN job_configurations jc ON jc.eval_template_id = et.id
    WHERE et.project_id = %s AND et.name ILIKE %s
    ORDER BY et.version DESC
    LIMIT 1
""", (PROJECT_ID, f"%{search_term}%"))
```

Display the current configuration.

### 2. Determine Change Category

Ask what to change, then categorize each change:

**Template-level changes** (require a new template version):
- `prompt` — evaluation prompt text
- `model` — model name
- `provider` — model provider
- `model_params` — temperature, max_tokens, etc.
- `vars` — template variables
- `output_schema` — reasoning/score descriptions

**Job-config-level changes** (in-place UPDATE, no new version needed):
- `filter` — trace filter conditions
- `variable_mapping` — variable-to-trace-field mapping
- `sampling` — evaluation sampling rate
- `delay` — execution delay
- `score_name` — score display name

### 3. Show Proposed Changes

Present changes for approval:

```
## Proposed Changes to: <evaluator_name>

**Change type**: <Template-level / Job-config-level>

**Current → New**:
  - prompt: <current first 50 chars...> → <new first 50 chars...>
  - model: gpt-4o → gpt-4o-mini

<If template-level>: This will create version <N+1> and deactivate old job configs.
<If job-config-level>: This will update the existing job configuration in place.

Proceed? (yes/no)
```

Wait for explicit user approval.

### 4A. Template-Level Update (New Version)

If any template-level field changed:

1. **Generate template and job config CUIDs**:

```python
from cuid2 import cuid_wrapper
cuid_generator = cuid_wrapper()
new_template_id = cuid_generator()
new_job_id = cuid_generator()
```

2. **Determine the next version**:

```sql
SELECT COALESCE(MAX(version), 0) + 1 AS next_version
FROM eval_templates
WHERE project_id = %s AND name = %s
```

3. **INSERT the new template version**:

```python
conn.autocommit = False
try:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO eval_templates (
                id, project_id, name, version, prompt, model, provider,
                model_params, vars, output_schema
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s::jsonb, %s, %s::jsonb
            )
        """, (
            new_template_id, PROJECT_ID, name, next_version,
            new_prompt, new_model, new_provider,
            json.dumps(new_model_params), new_vars, json.dumps(new_output_schema)
        ))
```

4. **Deactivate old job configurations**:

```python
        cur.execute("""
            UPDATE job_configurations
            SET status = 'INACTIVE', updated_at = NOW()
            WHERE project_id = %s
              AND eval_template_id IN (
                  SELECT id FROM eval_templates
                  WHERE project_id = %s AND name = %s
                    AND version < %s
              )
              AND status = 'ACTIVE'
        """, (PROJECT_ID, PROJECT_ID, name, next_version))
```

5. **INSERT the new template's job configuration**:

```python
        cur.execute("""
            INSERT INTO job_configurations (
                id, project_id, job_type, eval_template_id, score_name,
                filter, target_object, variable_mapping, sampling, delay,
                status, time_scope
            ) VALUES (
                %s, %s, 'EVAL', %s, %s,
                %s::jsonb, 'trace', %s::jsonb, %s, %s,
                'INACTIVE', ARRAY['NEW']
            )
        """, (
            new_job_id, PROJECT_ID, new_template_id, score_name,
            json.dumps(filter_config), json.dumps(variable_mapping),
            sampling, delay
        ))

    conn.commit()
except Exception:
    conn.rollback()
    raise
```

### 4B. Job-Config-Level Update (In-Place)

If only job-config-level fields changed, UPDATE the job configuration:

```python
cur.execute("""
    UPDATE job_configurations
    SET filter = %s::jsonb,
        variable_mapping = %s::jsonb,
        sampling = %s,
        delay = %s,
        score_name = %s,
        updated_at = NOW()
    WHERE id = %s AND project_id = %s
""", (
    json.dumps(new_filter), json.dumps(new_variable_mapping),
    new_sampling, new_delay, new_score_name,
    job_id, PROJECT_ID
))
conn.commit()
```

Include only changed fields in the SET clause.

### 5. Verify and Report

Run verification queries:

```sql
-- For template-level updates
SELECT id, name, version, model FROM eval_templates
WHERE id = %s AND project_id = %s;

-- For job-config-level updates
SELECT id, score_name, status, filter, sampling, delay FROM job_configurations
WHERE id = %s AND project_id = %s;
```

Report the result:

```
## Evaluator Updated Successfully

<If template-level>:
**New version**: <name> v<version> (id: <new_template_id>)
**New job config**: (id: <new_job_id>)
**Old job configs**: deactivated
**Status**: INACTIVE

<If job-config-level>:
**Job config updated**: (id: <job_id>)
**Changed fields**: <list of changed fields>

View in Langfuse: {LANGFUSE_HOST}/project/{PROJECT_ID}/settings/llm-as-a-judge

Would you like to activate this evaluator?
```

---

## Error Handling

- **Evaluator not found**: Report and suggest using `list-evaluators`.
- **Unique constraint violation**: Re-query max version and retry.
- **No job configuration exists**: Warn the user and offer to create one.
- **DB connection failed**: Attempt docker exec psql fallback before reporting.

---

## Cleanup

No temporary files are created by this skill.
