---
name: list-evaluators
description: >-
  This skill should be used when the user asks to list evaluators, see all
  evaluators, check what evaluators exist, or get an overview of LLM-as-a-Judge
  configurations in their Langfuse project. It queries eval_templates and
  job_configurations to produce a comprehensive summary.
---

# List Evaluators

Query all LLM-as-a-Judge evaluators in the project by joining `eval_templates`
(latest version per name) with their `job_configurations`. Report orphaned
templates and stale job configs.

---

## Prerequisites

Required inputs:

| Variable        | Example                              | Purpose                    |
|-----------------|--------------------------------------|----------------------------|
| `HOST`          | `http://localhost:3000`              | Langfuse base URL          |
| `PUBLIC_KEY`    | `pk-lf-...`                         | API Basic Auth username    |
| `SECRET_KEY`    | `sk-lf-...`                         | API Basic Auth password    |
| `PROJECT_ID`    | `clxxxxxxxxxxxxxxxxxxxxxxxxx`         | Multi-tenancy project ID   |
| `DB_CONN`       | `postgresql://user:pass@host:5432/db`| Direct DB connection       |

Validate credentials:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/scores?limit=1"
```

---

## Step 1 -- Query Latest-Version Templates with Job Configurations

### Option A: psycopg2 (Preferred)

```python
import psycopg2
import json

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# Latest evaluator version with job config
cur.execute("""
    WITH latest_templates AS (
        SELECT DISTINCT ON (name)
            id, name, version, model, provider, vars,
            output_schema, created_at, updated_at
        FROM eval_templates
        WHERE project_id = %s
        ORDER BY name, version DESC
    )
    SELECT
        lt.id AS template_id,
        lt.name,
        lt.version,
        lt.model,
        lt.provider,
        lt.vars,
        jc.id AS job_id,
        jc.score_name,
        jc.status,
        jc.sampling,
        jc.delay,
        jc.filter,
        jc.time_scope,
        jc.created_at AS job_created_at
    FROM latest_templates lt
    LEFT JOIN job_configurations jc
        ON jc.eval_template_id = lt.id
        AND jc.project_id = %s
    ORDER BY lt.name
""", (PROJECT_ID, PROJECT_ID))

rows = cur.fetchall()
```

### Option B: docker exec psql (Fallback)

```bash
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  WITH latest_templates AS (
      SELECT DISTINCT ON (name)
          id, name, version, model, provider, vars,
          output_schema, created_at, updated_at
      FROM eval_templates
      WHERE project_id = 'PROJECT_ID'
      ORDER BY name, version DESC
  )
  SELECT
      lt.id, lt.name, lt.version, lt.model, lt.provider, lt.vars,
      jc.id, jc.score_name, jc.status, jc.sampling, jc.delay,
      jc.filter, jc.time_scope, jc.created_at
  FROM latest_templates lt
  LEFT JOIN job_configurations jc
      ON jc.eval_template_id = lt.id
      AND jc.project_id = 'PROJECT_ID'
  ORDER BY lt.name;
"
```

---

## Step 2 -- Cross-Reference for Anomalies

### Orphaned templates (no job configuration)

```sql
SELECT et.id, et.name, et.version
FROM eval_templates et
LEFT JOIN job_configurations jc ON jc.eval_template_id = et.id
WHERE et.project_id = %s AND jc.id IS NULL
ORDER BY et.name, et.version DESC
```

Templates without job configs are not wired to evaluate traces.

### Stale job configs (pointing to non-latest template version)

```sql
WITH latest_versions AS (
    SELECT name, MAX(version) AS max_version
    FROM eval_templates
    WHERE project_id = %s
    GROUP BY name
)
SELECT jc.id AS job_id, et.name, et.version, lv.max_version, jc.status
FROM job_configurations jc
JOIN eval_templates et ON et.id = jc.eval_template_id
JOIN latest_versions lv ON lv.name = et.name
WHERE jc.project_id = %s
  AND et.version < lv.max_version
ORDER BY et.name
```

Stale job configs point to older template versions. If ACTIVE, they run an
outdated evaluation prompt.

---

## Step 3 -- Format and Present Output

### Main Evaluator Table

Present a markdown table:

```
| Name | Version | Model | Status | Score Name | Sampling | Delay (ms) | Filters |
|------|---------|-------|--------|------------|----------|------------|---------|
| factuality | 3 | gpt-4o | ACTIVE | factuality | 1.0 | 30000 | 2 conditions |
| no_markdown | 1 | gpt-4o | INACTIVE | no_markdown | 1.0 | 0 | none |
| tone | 2 | gpt-4o | INACTIVE | tone_professional | 0.5 | 10000 | 1 condition |
```

In Filters, show the condition count (e.g., "2 conditions") or "none" for an empty filter array.

### Anomalies Section

If orphaned templates or stale job configs are found, add a section:

```
### Anomalies

**Orphaned templates** (no job configuration):
- `test_evaluator` v1 (id: c...)

**Stale job configs** (pointing to non-latest version):
- `factuality` job (id: c...) points to v2, latest is v3 — status: INACTIVE
```

---

## Step 4 -- Summary

After the table, summarize:

- Total evaluator count (unique names with latest-version templates).
- Active/inactive split (count of ACTIVE vs INACTIVE job configurations).
- Orphaned template count (if any).
- Stale job config count (if any).
- Link: `{LANGFUSE_HOST}/project/{PROJECT_ID}/settings/llm-as-a-judge`

---

## Error Handling

- **No evaluators found**: Report no `eval_templates` exist; suggest `create-evaluator`.
- **DB connection failed**: Try docker exec psql fallback; report failure only if both methods fail.
- **Permission denied**: Report missing SELECT permission on `eval_templates` or `job_configurations`.

---

## Cleanup

No temporary files are created.
