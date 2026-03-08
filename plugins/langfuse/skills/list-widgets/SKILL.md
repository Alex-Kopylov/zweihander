---
name: list-widgets
description: >-
  This skill should be used when the user wants to list existing dashboard
  widgets in a Langfuse project, show widgets, see what widgets exist, get a
  widget inventory, or understand which widgets are deployed on which dashboards.
  Trigger phrases include "list widgets", "show widgets", "existing widgets",
  "what widgets exist", and "widget inventory". This is a shared skill used by
  both the data-explorer and widget-manager agents.
---

# List Dashboard Widgets

Retrieve all dashboard widgets from a Langfuse project and display them alongside their dashboard associations. This skill queries the PostgreSQL database directly since no public REST API endpoint exists for listing widgets.

## Prerequisites

Before executing, ensure the following credentials are available:

- **Project ID** -- the Langfuse project identifier (visible in the URL path)
- **Database connection** -- either a PostgreSQL connection string or Docker container access

## Step 1: Query All Widgets

Run the following SQL query against the Langfuse PostgreSQL database to retrieve all widgets belonging to the project:

```sql
SELECT dw.id, dw.name, dw.view, dw.chart_type, dw.created_at
FROM dashboard_widgets dw
WHERE dw.project_id = '{PROJECT_ID}'
ORDER BY dw.created_at DESC;
```

This returns every widget in the project regardless of whether it is placed on a dashboard.

## Step 2: Query All Dashboards

Retrieve all dashboards and their widget placement definitions:

```sql
SELECT d.id, d.name, d.definition
FROM dashboards d
WHERE d.project_id = '{PROJECT_ID}';
```

The `definition` column is a JSON object containing a `widgets` array. Each entry in that array has a `widgetId` field referencing a `dashboard_widgets.id`.

## Step 3: Cross-Reference Widgets to Dashboards

Parse each dashboard's `definition` JSON and extract the `widgetId` values from the `widgets` array:

```python
import json

# dashboard_rows: list of (id, name, definition) tuples from Step 2
widget_to_dashboards: dict[str, list[str]] = {}

for dashboard_id, dashboard_name, definition_json in dashboard_rows:
    definition = json.loads(definition_json) if isinstance(definition_json, str) else definition_json
    widgets = definition.get("widgets", [])
    for widget_entry in widgets:
        widget_id = widget_entry.get("widgetId")
        if widget_id:
            widget_to_dashboards.setdefault(widget_id, []).append(dashboard_name)
```

Map each widget ID to the list of dashboard names it appears on. Widgets not referenced by any dashboard are orphaned -- flag them in the output.

## Step 4: Format Output

Present the results as a formatted table combining widget metadata and dashboard associations:

```
| ID | Name | View | Chart Type | Dashboards |
|----|------|------|------------|------------|
| cmm66r6xu... | Avg Latency by Model | OBSERVATIONS | HORIZONTAL_BAR | Main Dashboard, Ops |
| cmm77s7yv... | Score Trend | SCORES_NUMERIC | LINE_TIME_SERIES | Main Dashboard |
| cmm88t8zw... | Orphaned Widget | TRACES | PIE | (none) |
```

Include the full CUID for the ID column (do not truncate). Mark widgets that appear on zero dashboards with `(none)` in the Dashboards column.

## Execution Methods

### Preferred: psycopg2 Python Script

Write and execute a Python script that connects to the database, runs both queries, performs the cross-referencing, and prints the formatted table:

```python
import json
import psycopg2

CONNECTION_STRING = "postgresql://user:pass@host:port/dbname"
PROJECT_ID = "your_project_id"

conn = psycopg2.connect(CONNECTION_STRING)
cur = conn.cursor()

# Fetch widgets
cur.execute(
    "SELECT id, name, view, chart_type, created_at "
    "FROM dashboard_widgets WHERE project_id = %s "
    "ORDER BY created_at DESC",
    (PROJECT_ID,),
)
widgets = cur.fetchall()

# Fetch dashboards
cur.execute(
    "SELECT id, name, definition "
    "FROM dashboards WHERE project_id = %s",
    (PROJECT_ID,),
)
dashboards = cur.fetchall()

conn.close()

# Build widget-to-dashboard mapping
widget_to_dashboards: dict[str, list[str]] = {}
for _dash_id, dash_name, definition in dashboards:
    defn = json.loads(definition) if isinstance(definition, str) else definition
    for entry in defn.get("widgets", []):
        wid = entry.get("widgetId")
        if wid:
            widget_to_dashboards.setdefault(wid, []).append(dash_name)

# Print table
print(f"{'ID':<30} {'Name':<35} {'View':<22} {'Chart Type':<22} {'Dashboards'}")
print("-" * 140)
for widget_id, name, view, chart_type, created_at in widgets:
    dash_names = widget_to_dashboards.get(widget_id, [])
    dash_str = ", ".join(dash_names) if dash_names else "(none)"
    print(f"{widget_id:<30} {name:<35} {view:<22} {chart_type:<22} {dash_str}")
```

Install `psycopg2-binary` if not already available:

```bash
uv add psycopg2-binary
```

### Fallback: docker exec psql

If psycopg2 is unavailable or the database is only reachable from within a Docker container, run the widget query via `docker exec`:

```bash
docker exec {CONTAINER_NAME} psql -U {DB_USER} -d {DB_NAME} -c \
  "SELECT dw.id, dw.name, dw.view, dw.chart_type, dw.created_at \
   FROM dashboard_widgets dw \
   WHERE dw.project_id = '{PROJECT_ID}' \
   ORDER BY dw.created_at DESC;"
```

Then run the dashboard query separately:

```bash
docker exec {CONTAINER_NAME} psql -U {DB_USER} -d {DB_NAME} -c \
  "SELECT d.id, d.name, d.definition \
   FROM dashboards d \
   WHERE d.project_id = '{PROJECT_ID}';"
```

Parse the psql output manually to perform the cross-referencing step. Note that JSON output from psql may require careful handling of escaping and line breaks.

## Output Interpretation

- **Orphaned widgets** (Dashboards = `(none)`) exist in the database but are not visible on any dashboard. They can be added to a dashboard using the `manage-dashboard` skill or deleted using the `delete-widget` skill.
- **Widgets on multiple dashboards** are shared -- modifying the widget config affects all dashboards that display it.
- **View column** indicates the data source: `TRACES`, `OBSERVATIONS`, `SCORES_NUMERIC`, or `SCORES_CATEGORICAL`.
- **Chart Type column** indicates the visualization: `LINE_TIME_SERIES`, `BAR_TIME_SERIES`, `HORIZONTAL_BAR`, `VERTICAL_BAR`, `PIE`, `NUMBER`, `HISTOGRAM`, or `PIVOT_TABLE`.

## Error Handling

- **Connection refused**: Verify the database connection string or Docker container name. Ensure the database is running and accessible.
- **Permission denied**: Check that the database user has SELECT privileges on `dashboard_widgets` and `dashboards` tables.
- **Empty results**: The project may have no widgets yet. Confirm the `PROJECT_ID` is correct by checking it against the Langfuse URL.
- **Malformed definition JSON**: If a dashboard's `definition` column contains invalid JSON, report the dashboard ID and name so the user can investigate manually.
