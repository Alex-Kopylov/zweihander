---
name: discover-traces
description: >-
  This skill should be used when the user asks to discover traces, list traces,
  find what traces exist, inspect trace names, explore trace tags, or check
  trace environments in their Langfuse project. It enumerates unique trace names,
  tags, environments, and user IDs via the Langfuse REST API with a
  direct-database fallback.
---

# Discover Traces

Enumerate all unique trace names, tags, environments, and user IDs present in a Langfuse project. Return a comprehensive summary so the caller understands the tracing landscape before filtering data, building widgets, or analyzing specific workflows.

---

## Prerequisites

Before executing any requests, ensure the following credentials are available (ask the user if missing):

| Variable        | Example                              | Purpose                    |
|-----------------|--------------------------------------|----------------------------|
| `HOST`          | `http://localhost:3000`              | Langfuse base URL          |
| `PUBLIC_KEY`    | `pk-lf-...`                         | API Basic Auth username    |
| `SECRET_KEY`    | `sk-lf-...`                         | API Basic Auth password    |
| `PROJECT_ID`    | `clxxxxxxxxxxxxxxxxxxxxxxxxx`         | Multi-tenancy project ID   |
| `DB_CONN`       | `postgresql://user:pass@host:5432/db`| Direct DB fallback (optional) |

Validate credentials before proceeding:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/traces?limit=1"
```

A `200` response confirms that authentication is valid. Any `401` or `403` response means the keys are incorrect -- report the error and ask the user to verify the public and secret keys.

---

## Step 1 -- Fetch Traces via REST API (Primary Path)

Call the Langfuse public traces endpoint with pagination. Start at page 1 and continue until all pages are consumed or enough data is collected for a representative summary.

```bash
PAGE=1
while true; do
  RESPONSE=$(curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
    "$HOST/api/public/traces?limit=100&page=$PAGE")

  COUNT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])))")

  if [ "$COUNT" -eq 0 ]; then
    break
  fi

  echo "$RESPONSE" >> /tmp/langfuse_traces_raw.json
  PAGE=$((PAGE + 1))
done
```

For each page response, the `data` array contains trace objects with the following relevant fields:

- `name` -- the trace name (e.g., `"chat-completion"`, `"document-qa"`, `"intake-generation"`)
- `tags` -- array of string tags (e.g., `["production", "v2", "experiment-a"]`)
- `environment` -- deployment environment string (e.g., `"production"`, `"staging"`, `"development"`)
- `userId` -- optional user identifier associated with the trace
- `sessionId` -- optional session grouping identifier
- `metadata` -- arbitrary metadata object attached to the trace

Process all collected pages to extract unique values:

```bash
python3 -c "
import json
from collections import Counter

traces = []
with open('/tmp/langfuse_traces_raw.json') as f:
    for line in f:
        try:
            page = json.loads(line)
            traces.extend(page.get('data', []))
        except json.JSONDecodeError:
            continue

# Collect unique values
names = Counter()
tags = Counter()
environments = Counter()
user_ids = set()

for t in traces:
    name = t.get('name') or '(unnamed)'
    names[name] += 1

    for tag in (t.get('tags') or []):
        tags[tag] += 1

    env = t.get('environment')
    if env:
        environments[env] += 1

    uid = t.get('userId')
    if uid:
        user_ids.add(uid)

print('=== TRACE NAMES ===')
for name, count in sorted(names.items(), key=lambda x: -x[1]):
    print(f'| {name} | {count} |')

print()
print('=== TAGS ===')
for tag, count in sorted(tags.items(), key=lambda x: -x[1]):
    print(f'| {tag} | {count} |')

print()
print('=== ENVIRONMENTS ===')
for env, count in sorted(environments.items(), key=lambda x: -x[1]):
    print(f'| {env} | {count} |')

print()
print('=== USER IDS ===')
print(f'Total unique user IDs: {len(user_ids)}')
if len(user_ids) <= 20:
    for uid in sorted(user_ids):
        print(f'  - {uid}')
else:
    for uid in sorted(user_ids)[:20]:
        print(f'  - {uid}')
    print(f'  ... and {len(user_ids) - 20} more')
"
```

### Handling Large Projects

If the project contains many thousands of traces and pagination becomes slow (more than 20 pages), abort the API loop after 20 pages. The collected sample of 2000 traces is sufficient to discover the unique names, tags, and environments. Note in the output that results are based on a sample and switch to the database fallback for exact counts if needed.

---

## Step 2 -- Database Fallback

When the REST API is unavailable, returns errors, or exact counts are needed for large projects, query the Langfuse PostgreSQL database directly.

### Option A: psycopg2 (Preferred)

Write and execute a Python script using parameterized queries:

```python
import psycopg2
import json

conn = psycopg2.connect("CONNECTION_STRING_HERE")
cur = conn.cursor()

# Unique trace names with counts
cur.execute("""
    SELECT COALESCE(name, '(unnamed)') as trace_name, COUNT(*) as cnt
    FROM traces
    WHERE project_id = %s
    GROUP BY trace_name
    ORDER BY cnt DESC
""", (PROJECT_ID,))
print("=== TRACE NAMES ===")
for row in cur.fetchall():
    print(f"| {row[0]} | {row[1]} |")

# Unique tags (tags are stored as a JSON array column)
cur.execute("""
    SELECT tag, COUNT(*) as cnt
    FROM traces, unnest(tags) AS tag
    WHERE project_id = %s
    GROUP BY tag
    ORDER BY cnt DESC
""", (PROJECT_ID,))
print("\n=== TAGS ===")
for row in cur.fetchall():
    print(f"| {row[0]} | {row[1]} |")

# Unique user IDs (count only, may be large)
cur.execute("""
    SELECT COUNT(DISTINCT user_id) as unique_users
    FROM traces
    WHERE project_id = %s AND user_id IS NOT NULL
""", (PROJECT_ID,))
print(f"\nUnique user IDs: {cur.fetchone()[0]}")

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
# Trace names
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT COALESCE(name, '(unnamed)'), COUNT(*)
  FROM traces
  WHERE project_id = 'PROJECT_ID'
  GROUP BY 1
  ORDER BY 2 DESC;
"

# Tags
docker exec CONTAINER_NAME psql -U USER -d DBNAME -t -A -F '|' -c "
  SELECT tag, COUNT(*)
  FROM traces, unnest(tags) AS tag
  WHERE project_id = 'PROJECT_ID'
  GROUP BY tag
  ORDER BY 2 DESC;
"

```

Parse the pipe-delimited output and format it into the standard tables.

---

## Step 3 -- Format and Present Output

Present the final results as three separate markdown tables plus a user ID summary.

### Trace Names

```
| Trace Name           | Count |
|----------------------|-------|
| chat-completion      | 3412  |
| document-qa          | 1870  |
| intake-generation    | 945   |
| (unnamed)            | 23    |
```

### Tags

```
| Tag                  | Count |
|----------------------|-------|
| production           | 4200  |
| v2                   | 2100  |
| experiment-a         | 500   |
| debug                | 12    |
```

### Environments

**Note:** Environment data is available via the REST API only. The database fallback does not query environments as this column exists only in ClickHouse.

```
| Environment          | Count |
|----------------------|-------|
| production           | 5100  |
| staging              | 780   |
| development          | 370   |
```

### User IDs

Report the total number of unique user IDs. If the count is 20 or fewer, list them all. If more than 20, list the first 20 alphabetically and note how many more exist.

---

## Step 4 -- Summary and Observations

After the tables, provide a brief textual summary:

- Total number of unique trace names.
- Total number of unique tags.
- Total number of distinct environments (API-only; not available via database fallback).
- Total number of unique user IDs.
- Any notable patterns such as: traces that lack a name (unnamed traces may indicate SDK misconfiguration), tags that appear on very few traces (possible test data), environments that have very low trace counts (possible staging/dev leftover data).
- If session IDs were observed in the API response, note whether sessions are being used and how many distinct sessions exist.

---

## Error Handling

- **Empty results**: If no traces are found, report that the project has no traces yet and suggest the user verify that their application is instrumented with the Langfuse SDK and sending trace data.
- **API timeout or 5xx errors**: Log the error, switch to the DB fallback path, and note to the user that the API was unreachable.
- **DB connection refused**: Report the connection error and ask the user to verify the connection string, database host reachability, and whether the Langfuse database container is running.
- **Permission denied on DB**: Report that the database user lacks SELECT permission on the `traces` table and suggest verifying the credentials.
- **Malformed tags column**: If the `unnest(tags)` query fails, the tags column format may differ. Fall back to fetching raw tag values and parsing them in Python.

---

## Cleanup

Remove any temporary files created during execution:

```bash
rm -f /tmp/langfuse_traces_raw.json
```
