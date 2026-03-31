---
name: discover-filter-options
description: >-
  This skill should be used when the user needs to build or configure trace
  filters for LLM-as-a-Judge evaluators. It discovers all filterable dimensions
  in the project (trace names, tags, environments, observation names, levels),
  helps construct the filter JSON array, validates the filter, and optionally
  runs a count query to show how many traces match. Trigger phrases include
  "discover filters", "what can I filter on", "build filter", "configure
  evaluator filter", "show filter options".
---

# Discover Filter Options

Discover all filterable dimensions in a Langfuse project and guide the user
through constructing a valid `filter` JSON array for `job_configurations`.

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

## Step 1 -- Discover All Filterable Dimensions

Run parallel queries to gather all possible filter values from the project.

### Option A: psycopg2 (Preferred)

```python
import psycopg2
import json

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# Trace names
cur.execute("""
    SELECT COALESCE(name, '(unnamed)') AS trace_name, COUNT(*) AS cnt
    FROM traces
    WHERE project_id = %s
    GROUP BY trace_name
    ORDER BY cnt DESC
""", (PROJECT_ID,))
trace_names = cur.fetchall()

# Tags
cur.execute("""
    SELECT tag, COUNT(*) AS cnt
    FROM traces, unnest(tags) AS tag
    WHERE project_id = %s
    GROUP BY tag
    ORDER BY cnt DESC
""", (PROJECT_ID,))
tags = cur.fetchall()

# Observation names (generations)
cur.execute("""
    SELECT COALESCE(name, '(unnamed)') AS obs_name, COUNT(*) AS cnt
    FROM observations
    WHERE project_id = %s AND type = 'GENERATION'
    GROUP BY obs_name
    ORDER BY cnt DESC
""", (PROJECT_ID,))
observation_names = cur.fetchall()

# Observation levels
cur.execute("""
    SELECT level, COUNT(*) AS cnt
    FROM observations
    WHERE project_id = %s
    GROUP BY level
    ORDER BY cnt DESC
""", (PROJECT_ID,))
observation_levels = cur.fetchall()

# Observation types
cur.execute("""
    SELECT type, COUNT(*) AS cnt
    FROM observations
    WHERE project_id = %s
    GROUP BY type
    ORDER BY cnt DESC
""", (PROJECT_ID,))
observation_types = cur.fetchall()

# Existing evaluator score names (for reference)
cur.execute("""
    SELECT DISTINCT score_name
    FROM job_configurations
    WHERE project_id = %s
    ORDER BY score_name
""", (PROJECT_ID,))
existing_score_names = cur.fetchall()

cur.close()
conn.close()
```

### Option B: docker exec psql (Fallback)

Run each query individually via docker exec:

```bash
# Trace names
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT COALESCE(name, '(unnamed)'), COUNT(*)
  FROM traces WHERE project_id = 'PROJECT_ID'
  GROUP BY 1 ORDER BY 2 DESC;
"

# Tags
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT tag, COUNT(*)
  FROM traces, unnest(tags) AS tag
  WHERE project_id = 'PROJECT_ID'
  GROUP BY tag ORDER BY 2 DESC;
"

# Observation names (generations)
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT COALESCE(name, '(unnamed)'), COUNT(*)
  FROM observations
  WHERE project_id = 'PROJECT_ID' AND type = 'GENERATION'
  GROUP BY 1 ORDER BY 2 DESC;
"

# Observation levels
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT level, COUNT(*)
  FROM observations WHERE project_id = 'PROJECT_ID'
  GROUP BY level ORDER BY 2 DESC;
"

# Observation types
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT type, COUNT(*)
  FROM observations WHERE project_id = 'PROJECT_ID'
  GROUP BY type ORDER BY 2 DESC;
"
```

---

## Step 2 -- Present Available Dimensions

Format the results as a structured summary:

```
## Available Filter Dimensions

### Trace Names (name)
| Name | Count |
|------|-------|
| celery:generate_html_controls | 3412 |
| celery:generate_ssp_controls | 1870 |
| chat-completion | 945 |

### Tags (tags)
| Tag | Count |
|-----|-------|
| production | 4200 |
| v2 | 2100 |
| experiment-a | 500 |

### Environments (environment)

**Note:** Environment data comes from the REST API, not direct DB queries. The `environment` column exists only in ClickHouse, not in the Postgres `traces` table.

| Environment | Count |
|-------------|-------|
| production | 5100 |
| staging | 780 |
| development | 370 |

### Generation Names (for variable_mapping objectName)
| Name | Count |
|------|-------|
| html_controls_generation | 3412 |
| ssp_controls_generation | 1870 |

### Observation Levels (level)
| Level | Count |
|-------|-------|
| DEFAULT | 5000 |
| WARNING | 150 |
| ERROR | 23 |

### Existing Evaluator Scores
| Score Name |
|------------|
| factuality |
| no_markdown |
```

---

## Step 3 -- Guide Filter Construction

Ask the user which dimensions they want to filter on. For each selected
dimension, present the appropriate operators:

### Filterable Columns Reference

| Column | Filter Type | Valid Operators | Value Format |
|--------|-------------|-----------------|--------------|
| `name` | `string` | `=`, `contains`, `does not contain`, `starts with`, `ends with` | single string |
| `name` | `stringOptions` | `any of`, `none of` | array of strings |
| `environment` | `stringOptions` | `any of`, `none of` | array of strings |
| `tags` | `arrayOptions` | `any of`, `none of`, `all of` | array of strings |
| `level` | `stringOptions` | `any of`, `none of` | array of: `DEFAULT`, `DEBUG`, `WARNING`, `ERROR` |
| `userId` | `string` | `=`, `contains`, `does not contain`, `starts with`, `ends with` | single string |

For each dimension the user selects:

1. Show available values from Step 1.
2. Ask which operator to use.
3. Ask which value(s) to match.
4. Compose the filter condition object.

---

## Step 4 -- Validate and Preview

### Compose the filter JSON

Assemble all selected conditions into a JSON array:

```json
[
  {
    "column": "name",
    "operator": "any of",
    "type": "stringOptions",
    "value": ["celery:generate_html_controls", "celery:generate_ssp_controls"]
  },
  {
    "column": "environment",
    "operator": "any of",
    "type": "stringOptions",
    "value": ["production"]
  }
]
```

### Explain what the filter matches

```
This filter will match traces where:
  - name is any of: "celery:generate_html_controls", "celery:generate_ssp_controls"
  AND
  - environment is any of: "production"
```

### Optionally run a count query

```sql
SELECT COUNT(*)
FROM traces
WHERE project_id = %s
  AND name IN ('celery:generate_html_controls', 'celery:generate_ssp_controls')
  AND environment IN ('production')
```

Report: "This filter matches approximately <count> existing traces."

---

## Step 5 -- Return the Filter JSON

Return the validated filter JSON for use by the calling skill
(`create-evaluator` or `update-evaluator`).

---

## Error Handling

- **No traces found**: Report that the project has no traces. Suggest verifying
  instrumentation.
- **No tags/environments**: Report that the dimension is empty. The user can
  still create a filter, but it may match nothing.
- **DB connection failed**: Attempt docker exec psql fallback before reporting.
- **Invalid operator for type**: Report the mismatch and show valid operators
  for the selected filter type.

---

## Cleanup

No temporary files are created by this skill.
