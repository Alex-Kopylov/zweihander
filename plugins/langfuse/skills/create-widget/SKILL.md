---
name: create-widget
description: >
  This skill should be used when the user wants to create a new Langfuse
  dashboard widget. Trigger phrases include "create widget", "add widget",
  "new visualization", "create chart", "add chart to dashboard". It handles
  ID generation, schema validation, SQL insertion, and post-creation
  verification of dashboard widgets.
---

# Create Langfuse Dashboard Widget

Create a new Langfuse dashboard widget by generating a valid configuration,
inserting it directly into the PostgreSQL `dashboard_widgets` table, and
verifying the result.

## Prerequisites

Ensure the following are available before proceeding:

- **Langfuse Host URL** and **Project ID** (from the parent plugin context).
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python libraries `cuid2` and `psycopg2-binary` installed. If missing, install
  via `uv add cuid2 psycopg2-binary`.

## Step-by-Step Procedure

### 1. Gather Widget Intent

Ask the user what they want to visualize. Typical intents include:

- "Average score over time"
- "Cost by model"
- "Latency p95 over time"
- "Trace count over time"
- "Big number: total cost"

Use the intent-to-config mapping table in
`references/widget-schema-reference.md` to translate the user's intent into
the correct combination of `view`, `metric`, `dimension`, and `chart_type`.

### 2. Generate a CUID for the Widget ID

```python
from cuid2 import cuid_wrapper

cuid_generator = cuid_wrapper()
widget_id = cuid_generator()
```

The generated CUID follows Langfuse's native ID format (e.g.,
`cmm66r6xu008up207601fgvpe`).

### 3. Build the Widget Configuration

Construct the JSON payloads for `dimensions`, `metrics`, `filters`, and
`chart_config` according to the schema in
`references/widget-schema-reference.md`.

**Dimensions** -- a JSON array of dimension objects:

```json
[{"field": "timestampDay"}]
```

**Metrics** -- a JSON array of metric objects:

```json
[{"field": "totalCost", "agg": "sum"}]
```

**Filters** -- a JSON array of filter objects (may be empty `[]`):

```json
[{"type": "string", "column": "scoreName", "operator": "starts with", "value": "self_eval:"}]
```

**Chart config** -- a JSON object whose shape depends on the chart type. Refer
to the chart config shapes section in `references/widget-schema-reference.md`.

### 4. Validate Against Schema

Before inserting, validate every field against the schema reference:

- Confirm `view` is one of: `TRACES`, `OBSERVATIONS`, `SCORES_NUMERIC`,
  `SCORES_CATEGORICAL`.
- Confirm `chart_type` is a valid `DashboardWidgetChartType` enum value.
- Confirm each dimension field is valid for the chosen view.
- Confirm each metric field and aggregation is valid for the chosen view.
- Confirm `chart_config` shape matches the chosen `chart_type`.

If any validation fails, report the specific violation and ask the user to
clarify.

### 5. Insert into PostgreSQL

Use psycopg2 with parameterized queries to perform the INSERT:

```sql
INSERT INTO dashboard_widgets (
  id, created_at, updated_at, created_by, updated_by,
  project_id, name, description, view, dimensions, metrics, filters,
  chart_type, chart_config
) VALUES (
  %(id)s, NOW(), NOW(), NULL, NULL,
  %(project_id)s, %(name)s, %(description)s,
  %(view)s, %(dimensions)s::jsonb, %(metrics)s::jsonb, %(filters)s::jsonb,
  %(chart_type)s, %(chart_config)s::jsonb
);
```

Pass all values as parameters to avoid SQL injection. JSON columns must be
serialized to strings via `json.dumps()` and cast to `::jsonb` in the query.

**Fallback** -- if psycopg2 is unavailable, use docker exec psql:

```bash
docker exec -i <container_name> psql -U <user> -d <dbname> -c "INSERT INTO ..."
```

Escape single quotes by doubling them (`''`) in string values when using the
psql fallback.

### 6. Verify the Insert

After insertion, verify the widget exists:

```sql
SELECT id, name, chart_type, view FROM dashboard_widgets
WHERE id = %(id)s AND project_id = %(project_id)s;
```

If the query returns a row, the widget was created successfully.

### 7. Optionally Add to a Dashboard

Ask the user whether to add this widget to an existing dashboard. If yes,
delegate to the `layout-widgets` skill to calculate grid placement and the
`manage-dashboard` skill to update the dashboard definition.

### 8. Provide the Widget URL

After successful creation, present the widget URL:

```
{LANGFUSE_HOST}/project/{PROJECT_ID}/widgets/{WIDGET_ID}?dashboardId={DASHBOARD_ID}
```

If no dashboard was specified, omit the `dashboardId` query parameter.

## Error Handling

- If the INSERT fails with a unique constraint violation, the CUID collided
  (extremely rare). Generate a new CUID and retry once.
- If the INSERT fails with a foreign key violation on `project_id`, the project
  does not exist. Report this to the user.
- If the database connection fails entirely, attempt the docker exec psql
  fallback before reporting failure.

## Reference

Consult `references/widget-schema-reference.md` for the complete list of valid
views, dimensions, metrics, filter operators, chart types, chart config shapes,
and the intent-to-config mapping table.
