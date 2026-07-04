---
name: discover-scores
description: >-
  Use when the user asks to discover, list, enumerate, or inspect Langfuse
  score names, data types, or sources. Enumerates unique score names, data
  types, and sources via the Langfuse REST API with a direct-database fallback.
---

# Discover Scores

Enumerate score names, data types, and sources in a Langfuse project. Return a deduplicated, grouped summary for use before building widgets, running analyses, or filtering traces.

---

## Prerequisites

Before requests, ensure these credentials are available; ask the user if any are missing:

| Variable        | Example                              | Purpose                    |
|-----------------|--------------------------------------|----------------------------|
| `HOST`          | `http://localhost:3000`              | Langfuse base URL          |
| `PUBLIC_KEY`    | `pk-lf-...`                         | API Basic Auth username    |
| `SECRET_KEY`    | `sk-lf-...`                         | API Basic Auth password    |
| `PROJECT_ID`    | `clxxxxxxxxxxxxxxxxxxxxxxxxx`         | Multi-tenancy project ID   |
| `DB_CONN`       | `postgresql://user:pass@host:5432/db`| Direct DB fallback (optional) |

Validate credentials before proceeding by running:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/scores?limit=1"
```

A `200` confirms authentication. For `401` or `403`, report the error and ask the user to verify the public and secret keys.

---

## Step 1 -- Fetch Scores via REST API (Primary Path)

Call the Langfuse public scores endpoint from page 1 until all pages are consumed.

```bash
PAGE=1
while true; do
  RESPONSE=$(curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
    "$HOST/api/public/scores?limit=100&page=$PAGE")

  # Parse the response -- extract the data array length
  COUNT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))")

  if [ "$COUNT" -eq 0 ]; then
    break
  fi

  echo "$RESPONSE" >> /tmp/langfuse_scores_raw.json
  PAGE=$((PAGE + 1))
done
```

Each page's `data` array contains score objects with these relevant fields:

- `name` -- the score name (e.g., `"correctness"`, `"self_eval:relevance"`)
- `dataType` -- either `NUMERIC` or `CATEGORICAL`
- `source` -- one of `API`, `ANNOTATION`, or `EVAL`
- `value` -- the numeric or string value
- `traceId` -- the associated trace

Extract unique combinations from the collected pages:

```bash
python3 -c "
import json, sys
from collections import Counter

scores = []
with open('/tmp/langfuse_scores_raw.json') as f:
    for line in f:
        try:
            page = json.loads(line)
            scores.extend(page.get('data', []))
        except json.JSONDecodeError:
            continue

# Build a summary keyed by (name, dataType, source)
summary = Counter()
for s in scores:
    key = (s.get('name',''), s.get('dataType',''), s.get('source',''))
    summary[key] += 1

# Sort by name, then source
for (name, dtype, source), count in sorted(summary.items()):
    print(f'| {name} | {dtype} | {source} | {count} |')
"
```

### Handling Large Projects

If pagination exceeds 20 pages, abort the API loop, switch to the Step 2 database fallback, and log that the API was too slow.

---

## Step 2 -- Database Fallback

When the REST API is unavailable, returns errors, or is too slow, query the Langfuse PostgreSQL database directly.

### Option A: psycopg2 (Preferred)

Run a Python script with a parameterized query:

```python
import psycopg2

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()
cur.execute("""
    SELECT name, data_type, source, COUNT(*) as cnt
    FROM scores
    WHERE project_id = %s
    GROUP BY name, data_type, source
    ORDER BY name, source
""", (PROJECT_ID,))

rows = cur.fetchall()
for row in rows:
    print(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")

cur.close()
conn.close()
```

If `psycopg2` is missing:

```bash
uv add psycopg2-binary
```

### Option B: docker exec psql (Fallback)

If the database is only reachable from a Docker container:

```bash
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT name, data_type, source, COUNT(*) as cnt
  FROM scores
  WHERE project_id = 'PROJECT_ID'
  GROUP BY name, data_type, source
  ORDER BY name, source;
"
```

Parse the pipe-delimited output and format it into the standard table.

---

## Step 3 -- Group and Classify Results

After collecting API or DB data, group scores by source:

1. **API scores** -- scores ingested programmatically via the Langfuse SDK or REST API during trace creation.
2. **ANNOTATION scores** -- scores added manually by human annotators through the Langfuse UI.
3. **EVAL scores** -- scores produced by Langfuse's built-in evaluation pipelines (e.g., LLM-as-judge evaluators).

Within each group, note whether each score is `NUMERIC` (continuous floats, typically 0-1 but not limited to that range) or `CATEGORICAL` (labels such as `"pass"`, `"fail"`, `"good"`, `"bad"`).

---

## Step 4 -- Format and Present Output

Present the final results as a markdown table:

```
| Score Name           | Data Type   | Source     | Count |
|----------------------|-------------|------------|-------|
| correctness          | NUMERIC     | API        | 1523  |
| correctness          | NUMERIC     | EVAL       | 842   |
| relevance            | NUMERIC     | API        | 1520  |
| self_eval:format     | CATEGORICAL | API        | 760   |
| human_review         | NUMERIC     | ANNOTATION | 45    |
```

After the table, provide a brief summary:

- Total number of unique score names found.
- Breakdown by data type: how many are NUMERIC vs CATEGORICAL.
- Breakdown by source: how many come from API, ANNOTATION, EVAL.
- Any notable patterns (e.g., scores that exist under multiple sources, scores with very low counts that might be test data).

---

## Error Handling

- **Empty results**: If no scores are found, report that the project has no scores yet and suggest the user check that scoring is configured in their Langfuse SDK integration or evaluation pipelines.
- **API timeout or 5xx errors**: Log the error, switch to the DB fallback path, and note to the user that the API was unreachable.
- **DB connection refused**: Report the connection error and ask the user to verify the connection string, database host reachability, and whether the Langfuse database container is running.
- **Permission denied on DB**: Report that the database user lacks SELECT permission on the `scores` table and suggest verifying the credentials.

---

## Cleanup

Remove temporary files:

```bash
rm -f /tmp/langfuse_scores_raw.json
```
