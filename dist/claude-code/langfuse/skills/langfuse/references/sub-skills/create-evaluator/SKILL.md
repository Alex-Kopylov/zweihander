---
name: create-evaluator
description: >
  Use when the user wants to create a Langfuse LLM-as-a-Judge evaluator.
  Trigger phrases: "create evaluator", "add evaluator", "new evaluation",
  "set up evaluation criteria", "create judge". Handles prompt composition,
  schema validation, ID generation, SQL insertion into eval_templates and
  job_configurations, and post-creation verification.
---

# Create LLM-as-a-Judge Evaluator

Insert a Langfuse LLM-as-a-Judge evaluator directly into PostgreSQL by creating
an `eval_template` and matching `job_configuration`.

---

## Prerequisites

Ensure the following are available before proceeding:

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python libraries `cuid2` and `psycopg2-binary` installed. If missing, install
  via `uv add cuid2 psycopg2-binary`.

Consult `references/evaluator-schema-reference.md` for complete schema details,
format rules, and common patterns.

---

## Step-by-Step Procedure

### 1. Gather Intent

Ask the user what they want to evaluate. Common intents:

- Factual accuracy of outputs against input context
- Relevance of answers to questions
- Tone or style compliance
- Absence of markdown formatting
- Completeness of response
- Custom evaluation criteria

### 2. Compose Evaluation Prompt

Work with the user to compose or accept an evaluation prompt. The prompt must:

- Use `{{variable}}` syntax for template variables (e.g., `{{input}}`, `{{output}}`).
- Include clear instructions for the LLM judge.
- Specify the scoring criteria and scale.
- Request JSON output with `reasoning` and `score` fields.

Extract the list of `{{variables}}` from the prompt for the `vars` array.

### 3. Define Output Schema

Configure the `output_schema` with descriptive values for `reasoning` and `score`:

```json
{"reasoning": "Step-by-step analysis explaining the score", "score": "Score between 0 and 1"}
```

The values are LLM instructions, not type descriptors. Richer descriptions
produce better evaluations. See `references/evaluator-schema-reference.md` for
correct vs incorrect examples.

### 4. Configure Variable Mapping

For each `{{variable}}` extracted from the prompt, configure a variable mapping
entry:

- **Source object**: `trace` (default), `generation`, `span`, or other observation type.
- **Column**: `input`, `output`, or `metadata`.
- **Object name**: Required for non-trace objects (e.g., a specific generation name).
- **JSON selector**: Optional JSONPath for sub-field extraction.

Use `discover-traces` to help the user identify available trace names and
observation names if needed.

### 5. Configure Model and Provider

Set the model and provider. Defaults:

- **Model**: `gpt-4o`
- **Provider**: `azure`
- **Model params**: `{"temperature": 0, "max_tokens": 500}`

Verify the model is configured in the project:

```sql
SELECT provider, adapter, custom_models FROM llm_api_keys
WHERE project_id = %s;
```

### 6. Configure Trace Filters

Ask whether to restrict which traces this evaluator runs on. If yes, delegate to
`discover-filter-options` to identify filter dimensions (trace names, tags,
environments) and construct the filter JSON. If not, use `[]`.

### 7. Configure Job Parameters

- **score_name**: Name of the score in Langfuse UI (default: same as evaluator name).
- **sampling**: Fraction of matching traces to evaluate (default: `1.0` = 100%).
- **delay**: Milliseconds to wait before executing (default: `0`).
- **target_object**: Always `'trace'`.

### 8. Show Proposed Configuration

Present the complete proposed configuration for user approval:

```
## Proposed Evaluator: <name>

**Template**:
  - Name: <name>
  - Model: <model> (<provider>)
  - Variables: <var1>, <var2>
  - Output Schema: {"reasoning": "...", "score": "..."}

**Prompt**:
<prompt text>

**Job Configuration**:
  - Score Name: <score_name>
  - Sampling: <sampling>
  - Delay: <delay>ms
  - Status: INACTIVE (safety default)
  - Time Scope: ['NEW']
  - Filters: <filter summary or "none">
  - Variable Mapping: <mapping summary>

Proceed with creation? (yes/no)
```

Wait for explicit user approval before writing to the database.

### 9. Check for Existing Evaluator

Before inserting, check if an evaluator with the same name already exists:

```sql
SELECT id, name, version FROM eval_templates
WHERE project_id = %s AND name = %s
ORDER BY version DESC LIMIT 1
```

- If it exists, determine the next version number (`max_version + 1`).
- If it does not exist, use version `1`.

### 10. Generate CUIDs

Generate two CUIDs — one for the template, one for the job configuration:

```python
from cuid2 import cuid_wrapper

cuid_generator = cuid_wrapper()
template_id = cuid_generator()
job_config_id = cuid_generator()
```

### 11. INSERT eval_template

### Option A: psycopg2 (Preferred)

```python
import psycopg2
import json

conn = psycopg2.connect("CONNECTION_STRING_HERE")
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
            template_id, PROJECT_ID, name, version, prompt, model, provider,
            json.dumps(model_params), vars_array, json.dumps(output_schema)
        ))
```

### Option B: docker exec psql (Fallback)

```bash
docker exec -i CONTAINER_NAME psql -U USER -d DBNAME -c "
  INSERT INTO eval_templates (
      id, project_id, name, version, prompt, model, provider,
      model_params, vars, output_schema
  ) VALUES (
      'TEMPLATE_ID', 'PROJECT_ID', 'NAME', VERSION,
      'PROMPT_TEXT',
      'MODEL', 'PROVIDER',
      '{\"temperature\": 0, \"max_tokens\": 500}'::jsonb,
      ARRAY['var1', 'var2'],
      '{\"reasoning\": \"...\", \"score\": \"...\"}'::jsonb
  );
"
```

### 12. INSERT job_configuration

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
            job_config_id, PROJECT_ID, template_id, score_name,
            json.dumps(filter_config), json.dumps(variable_mapping),
            sampling, delay
        ))

    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

### 13. Verify Insertion

Run verification queries to confirm both records were created:

```sql
SELECT id, name, version, model FROM eval_templates
WHERE id = %s AND project_id = %s;

SELECT id, score_name, status, eval_template_id FROM job_configurations
WHERE id = %s AND project_id = %s;
```

Both queries must return exactly one row.

### 14. Report Success

Present a success summary:

```
## Evaluator Created Successfully

**Template**: <name> v<version> (id: <template_id>)
**Job Config**: <score_name> (id: <job_config_id>)
**Status**: INACTIVE

View in Langfuse: {LANGFUSE_HOST}/project/{PROJECT_ID}/settings/llm-as-a-judge

Would you like to activate this evaluator now?
```

If the user wants to activate, delegate to the `toggle-evaluator-status` skill.

---

## Error Handling

- **Unique constraint violation on eval_templates**: An evaluator with the same
  name and version already exists. Re-query the max version and retry with the
  correct next version.
- **Foreign key violation on job_configurations.eval_template_id**: The template
  INSERT failed silently. Roll back and report.
- **Model not configured**: If the model/provider check fails, warn the user
  that the model must be configured in Langfuse's LLM API keys before the
  evaluator can execute.
- **DB connection failed**: Attempt docker exec psql fallback before reporting
  failure.
