---
name: inspect-evaluator
description: >-
  This skill should be used when the user asks to inspect an evaluator, view
  evaluator details, show evaluator configuration, check an evaluator's prompt,
  or see the full setup of a specific LLM-as-a-Judge evaluator. It shows the
  complete template, version history, and associated job configurations.
---

# Inspect Evaluator

Look up a specific LLM-as-a-Judge evaluator by name or ID, display its full
configuration (prompt, variables, output schema, model, filters), version
history, and associated job configurations.

---

## Prerequisites

Ensure the following are available before proceeding:

| Variable        | Example                              | Purpose                    |
|-----------------|--------------------------------------|----------------------------|
| `HOST`          | `http://localhost:3000`              | Langfuse base URL          |
| `PUBLIC_KEY`    | `pk-lf-...`                         | API Basic Auth username    |
| `SECRET_KEY`    | `sk-lf-...`                         | API Basic Auth password    |
| `PROJECT_ID`    | `clxxxxxxxxxxxxxxxxxxxxxxxxx`         | Multi-tenancy project ID   |
| `DB_CONN`       | `postgresql://user:pass@host:5432/db`| Direct DB connection       |

---

## Step 1 -- Identify the Evaluator

Accept a name or ID from the user. Use ILIKE for fuzzy matching on name:

### Option A: psycopg2 (Preferred)

```python
import psycopg2
import json

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# Search by name (fuzzy) — returns latest version by default
cur.execute("""
    SELECT id, name, version, prompt, model, provider,
           model_params, vars, output_schema, created_at, updated_at
    FROM eval_templates
    WHERE project_id = %s AND name ILIKE %s
    ORDER BY version DESC
    LIMIT 1
""", (PROJECT_ID, f"%{search_term}%"))

template = cur.fetchone()
```

If searching by ID:

```python
cur.execute("""
    SELECT id, name, version, prompt, model, provider,
           model_params, vars, output_schema, created_at, updated_at
    FROM eval_templates
    WHERE project_id = %s AND id = %s
""", (PROJECT_ID, template_id))
```

### Option B: docker exec psql (Fallback)

```bash
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT id, name, version, prompt, model, provider,
         model_params, vars, output_schema, created_at, updated_at
  FROM eval_templates
  WHERE project_id = 'PROJECT_ID' AND name ILIKE '%SEARCH_TERM%'
  ORDER BY version DESC
  LIMIT 1;
"
```

If multiple evaluators match the fuzzy search, list them all and ask the user
to select the specific one.

---

## Step 2 -- Display Full Template Detail

Present the template configuration in a structured format:

```
## Evaluator: factuality (v3)

**Template ID**: clxxxxxxxxxxxxxxxxxxxxxxxxx
**Model**: gpt-4o (azure)
**Model Params**: {"temperature": 0, "max_tokens": 500}
**Variables**: input, output
**Output Schema**:
  - reasoning: "Step-by-step analysis of factual consistency"
  - score: "Score between 0 and 1"
**Created**: 2024-12-15 10:30:00
**Updated**: 2024-12-15 10:30:00

### Prompt

<prompt text displayed in a code block>
```

---

## Step 3 -- Fetch Version History

Query all versions of this evaluator:

```python
cur.execute("""
    SELECT version, id, model, provider, created_at,
           LENGTH(prompt) AS prompt_length
    FROM eval_templates
    WHERE project_id = %s AND name = %s
    ORDER BY version DESC
""", (PROJECT_ID, evaluator_name))

versions = cur.fetchall()
```

Present as a version history table:

```
### Version History

| Version | Template ID | Model | Provider | Created | Prompt Length |
|---------|-------------|-------|----------|---------|---------------|
| 3 | cmm66... | gpt-4o | azure | 2024-12-15 | 450 chars |
| 2 | cmm55... | gpt-4o | azure | 2024-12-10 | 380 chars |
| 1 | cmm44... | gpt-3.5-turbo | azure | 2024-12-01 | 320 chars |
```

---

## Step 4 -- Fetch Associated Job Configurations

Query all job configurations linked to any version of this evaluator:

```python
cur.execute("""
    SELECT jc.id, jc.eval_template_id, et.version,
           jc.score_name, jc.status, jc.filter, jc.variable_mapping,
           jc.sampling, jc.delay, jc.time_scope, jc.created_at
    FROM job_configurations jc
    JOIN eval_templates et ON et.id = jc.eval_template_id
    WHERE jc.project_id = %s AND et.name = %s
    ORDER BY et.version DESC, jc.created_at DESC
""", (PROJECT_ID, evaluator_name))

jobs = cur.fetchall()
```

Present job configuration details:

```
### Job Configurations

**Job ID**: cmm77...
**Template Version**: 3
**Score Name**: factuality
**Status**: ACTIVE
**Sampling**: 1.0 (100%)
**Delay**: 30000ms (30s)
**Time Scope**: ['NEW']

**Variable Mapping**:
  - {{input}} → trace.input
  - {{output}} → trace.output

**Filters**:
  - trace_name any of ["celery:generate_html_controls"]
  - environment any of ["production"]
```

Format the variable_mapping and filter JSON into human-readable descriptions.

---

## Step 5 -- Provide URL

```
**Evaluator settings**: {LANGFUSE_HOST}/project/{PROJECT_ID}/settings/llm-as-a-judge
```

---

## Error Handling

- **Evaluator not found**: If no match is found, report this and suggest using
  `list-evaluators` to see available evaluators.
- **Multiple matches**: If ILIKE returns multiple different evaluator names,
  list them all and ask the user to specify which one.
- **DB connection failed**: Attempt docker exec psql fallback before reporting
  failure.

---

## Cleanup

No temporary files are created by this skill.
