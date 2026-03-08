---
name: discover-models
description: >-
  This skill should be used when the user asks to discover models, list models,
  find what models are available, check model pricing, or see which models are
  actually used in their Langfuse project. It lists both the registered model
  definitions (with pricing) and the models observed in actual trace data via
  the Langfuse REST API with a direct-database fallback.
---

# Discover Models

List all model definitions registered in a Langfuse project (including pricing configuration) and cross-reference them against models actually observed in trace data. Return a unified view so the caller understands which models are available, how they are priced, and which are actively generating observations.

---

## Prerequisites

Before executing any requests, ensure the following credentials are available (ask the user if missing):

| Variable        | Example                              | Purpose                    |
|-----------------|--------------------------------------|----------------------------|
| `HOST`          | `http://localhost:3000`              | Langfuse base URL          |
| `PUBLIC_KEY`    | `pk-lf-...`                         | API Basic Auth username    |
| `SECRET_KEY`    | `sk-lf-...`                         | API Basic Auth password    |
| `PROJECT_ID`    | `cmm66r6xu008up207601fgvpe`         | Multi-tenancy project ID   |
| `DB_CONN`       | `postgresql://user:pass@host:5432/db`| Direct DB fallback (optional) |

Validate credentials before proceeding:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/models?limit=1"
```

A `200` response confirms that authentication is valid. Any `401` or `403` response means the keys are incorrect -- report the error and ask the user to verify the public and secret keys.

---

## Step 1 -- Fetch Registered Model Definitions via REST API

Call the Langfuse public models endpoint to retrieve all model definitions with their pricing configuration. Paginate until all models are collected.

```bash
PAGE=1
while true; do
  RESPONSE=$(curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
    "$HOST/api/public/models?limit=100&page=$PAGE")

  COUNT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))")

  if [ "$COUNT" -eq 0 ]; then
    break
  fi

  echo "$RESPONSE" >> /tmp/langfuse_models_raw.json
  PAGE=$((PAGE + 1))
done
```

For each model definition, the relevant fields are:

- `modelName` -- the canonical model name (e.g., `"gpt-4o"`, `"claude-sonnet-4-20250514"`)
- `unit` -- pricing unit, typically `"TOKENS"` or `"CHARACTERS"`
- `inputPrice` -- cost per unit for input/prompt tokens (decimal, e.g., `0.000003`)
- `outputPrice` -- cost per unit for output/completion tokens (decimal, e.g., `0.000015`)
- `totalPrice` -- optional flat cost per request (some models use this instead of per-token pricing)
- `matchPattern` -- regex pattern used to match observation model strings to this definition

Parse the collected model definitions:

```bash
python3 -c "
import json

models = []
with open('/tmp/langfuse_models_raw.json') as f:
    for line in f:
        try:
            page = json.loads(line)
            models.extend(page.get('data', []))
        except json.JSONDecodeError:
            continue

print('=== REGISTERED MODELS ===')
for m in sorted(models, key=lambda x: x.get('modelName', '')):
    name = m.get('modelName', '(unknown)')
    unit = m.get('unit', 'N/A')
    inp = m.get('inputPrice')
    out = m.get('outputPrice')
    inp_str = f'{inp}' if inp is not None else 'N/A'
    out_str = f'{out}' if out is not None else 'N/A'
    print(f'| {name} | {unit} | {inp_str} | {out_str} |')
"
```

---

## Step 2 -- Discover Models Actually Used in Observations

The registered model definitions represent what Langfuse knows about for pricing. However, observations may reference model strings that do not match any registered definition (resulting in missing cost calculations). Discover which models are actually used in observations.

### Via REST API

Fetch a sample of observations and extract unique model values:

```bash
PAGE=1
while true; do
  RESPONSE=$(curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
    "$HOST/api/public/observations?limit=100&page=$PAGE")

  COUNT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))")

  if [ "$COUNT" -eq 0 ]; then
    break
  fi

  echo "$RESPONSE" >> /tmp/langfuse_observations_raw.json
  PAGE=$((PAGE + 1))

  # Limit to 20 pages for sampling
  if [ "$PAGE" -gt 20 ]; then
    break
  fi
done
```

Extract unique model names from the observations:

```bash
python3 -c "
import json
from collections import Counter

observations = []
with open('/tmp/langfuse_observations_raw.json') as f:
    for line in f:
        try:
            page = json.loads(line)
            observations.extend(page.get('data', []))
        except json.JSONDecodeError:
            continue

model_counts = Counter()
for obs in observations:
    model = obs.get('model')
    if model:
        model_counts[model] += 1

print('=== MODELS IN OBSERVATIONS ===')
for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
    print(f'| {model} | {count} |')
"
```

For exact counts on large projects, use the database fallback in Step 3.

---

## Step 3 -- Database Fallback

When the REST API is unavailable, returns errors, or exact counts are needed, query the PostgreSQL database directly.

### Option A: psycopg2 (Preferred)

Write and execute a Python script using parameterized queries:

```python
import psycopg2

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# Registered model definitions
cur.execute("""
    SELECT model_name, unit, input_price, output_price
    FROM models
    WHERE project_id = %s
    ORDER BY model_name
""", (PROJECT_ID,))
print("=== REGISTERED MODELS ===")
for row in cur.fetchall():
    name, unit, inp, out = row
    inp_str = str(inp) if inp is not None else "N/A"
    out_str = str(out) if out is not None else "N/A"
    print(f"| {name} | {unit or 'N/A'} | {inp_str} | {out_str} |")

# Models actually used in observations
cur.execute("""
    SELECT model, COUNT(*) as cnt
    FROM observations
    WHERE project_id = %s AND model IS NOT NULL
    GROUP BY model
    ORDER BY cnt DESC
""", (PROJECT_ID,))
print("\n=== MODELS IN OBSERVATIONS ===")
for row in cur.fetchall():
    print(f"| {row[0]} | {row[1]} |")

cur.close()
conn.close()
```

If `psycopg2` is not installed, install it first:

```bash
uv add psycopg2-binary
```

### Option B: docker exec psql (Fallback)

When the database is only reachable from within a Docker container:

```bash
# Registered models
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT model_name, unit, input_price, output_price
  FROM models
  WHERE project_id = 'PROJECT_ID'
  ORDER BY model_name;
"

# Models used in observations
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT model, COUNT(*) as cnt
  FROM observations
  WHERE project_id = 'PROJECT_ID' AND model IS NOT NULL
  GROUP BY model
  ORDER BY cnt DESC;
"
```

Parse the pipe-delimited output and format it into the standard tables.

**Note:** The `latency` field is computed, not stored. In Postgres queries, compute it as `EXTRACT(EPOCH FROM (end_time - start_time))` (returns seconds as a float). The REST API returns `latency` as a pre-computed field.

---

## Step 4 -- Cross-Reference and Merge

After collecting both registered model definitions and observed model names, merge them into a single unified table. For each model, indicate whether it has a registered pricing definition and whether it appears in actual observations.

```bash
python3 -c "
import json
from collections import Counter

# Load registered models
registered = {}
try:
    with open('/tmp/langfuse_models_raw.json') as f:
        for line in f:
            try:
                page = json.loads(line)
                for m in page.get('data', []):
                    name = m.get('modelName', '')
                    registered[name] = {
                        'inputPrice': m.get('inputPrice'),
                        'outputPrice': m.get('outputPrice'),
                    }
            except json.JSONDecodeError:
                continue
except FileNotFoundError:
    pass

# Load observed models
observed = Counter()
try:
    with open('/tmp/langfuse_observations_raw.json') as f:
        for line in f:
            try:
                page = json.loads(line)
                for obs in page.get('data', []):
                    model = obs.get('model')
                    if model:
                        observed[model] += 1
            except json.JSONDecodeError:
                continue
except FileNotFoundError:
    pass

# Merge into unified view
all_models = set(registered.keys()) | set(observed.keys())

print('| Model Name | Input Price | Output Price | Used in Observations |')
print('|------------|-------------|--------------|----------------------|')
for name in sorted(all_models):
    reg = registered.get(name)
    inp = str(reg['inputPrice']) if reg and reg['inputPrice'] is not None else 'N/A'
    out = str(reg['outputPrice']) if reg and reg['outputPrice'] is not None else 'N/A'
    obs_count = observed.get(name, 0)
    used = f'Yes ({obs_count})' if obs_count > 0 else 'No'
    print(f'| {name} | {inp} | {out} | {used} |')
"
```

---

## Step 5 -- Format and Present Output

Present the final merged result as a single markdown table:

```
| Model Name                  | Input Price | Output Price | Used in Observations |
|-----------------------------|-------------|--------------|----------------------|
| claude-sonnet-4-20250514    | 0.000003    | 0.000015     | Yes (1245)           |
| gpt-4o                      | 0.000005    | 0.000015     | Yes (3400)           |
| gpt-4o-mini                 | 0.00000015  | 0.0000006    | Yes (890)            |
| text-embedding-3-small      | 0.00000002  | N/A          | Yes (5600)           |
| custom-fine-tuned-v1        | N/A         | N/A          | Yes (12)             |
```

After the table, provide a brief summary:

- Total number of registered model definitions.
- Total number of distinct models observed in trace data.
- Any models appearing in observations that lack a registered pricing definition -- flag these explicitly because their cost calculations will be missing in Langfuse. Recommend the user register these models via the Langfuse UI or API to enable accurate cost tracking.
- Any registered models that have zero observations -- these may be outdated definitions or models not yet deployed.
- If pricing is configured, note the relative cost difference between the most and least expensive models to help the user understand cost distribution.

---

## Error Handling

- **Empty model definitions**: If no model definitions are found in the registry, this is normal for projects that rely on Langfuse's built-in model matching. Note this and focus on the observation-based model discovery.
- **Empty observations**: If no observations exist, report that the project has no observation data yet and suggest verifying that the application is instrumented and generating LLM calls through the Langfuse SDK.
- **API timeout or 5xx errors**: Log the error, switch to the DB fallback path, and note to the user that the API was unreachable.
- **DB connection refused**: Report the connection error and ask the user to verify the connection string, database host reachability, and whether the Langfuse database container is running.
- **Permission denied on DB**: Report that the database user lacks SELECT permission on the `models` or `observations` table and suggest verifying the credentials.
- **Models endpoint returns 404**: Some older Langfuse versions may not expose the `/api/public/models` endpoint. Fall back to the database query for registered models.

---

## Cleanup

Remove any temporary files created during execution:

```bash
rm -f /tmp/langfuse_models_raw.json /tmp/langfuse_observations_raw.json
```
