---
name: update-widget
description: >
  Use when the user wants to update or modify an existing Langfuse dashboard
  widget configuration. Triggers: "update widget", "modify widget", "change
  widget", "edit widget configuration". It reads the current widget state,
  accepts changes conversationally, validates the new configuration, and applies
  the UPDATE.
---

# Update Langfuse Dashboard Widget



## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python library `psycopg2-binary`; install with `uv add psycopg2-binary` if needed.
- The widget ID to update. If unknown, ask the user or use the `list-widgets`
  skill to enumerate available widgets.

## Step-by-Step Procedure

### 1. Identify the Target Widget

Accept the widget ID from the user. If the user provides a widget name instead
of an ID, look it up:

```sql
SELECT id, name, view, chart_type, dimensions, metrics, filters, chart_config, description
FROM dashboard_widgets
WHERE project_id = %(project_id)s
  AND (id = %(identifier)s OR name ILIKE %(identifier)s)
ORDER BY created_at DESC
LIMIT 5;
```

If multiple matches are found, present them and ask the user to select one.

### 2. Read and Display Current Configuration

Fetch the full current configuration:

```sql
SELECT id, name, description, view, dimensions, metrics, filters,
       chart_type, chart_config, created_at, updated_at
FROM dashboard_widgets
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

Present the current configuration in a readable format, including name,
description, data-source view (TRACES, OBSERVATIONS, etc.), chart type,
grouping/bucketing dimensions, metric aggregations, active filters, and
type-specific chart config.

### 3. Accept Changes Conversationally

Ask the user what they want to change. Common modification patterns:

- Change the chart type (e.g., from line to bar)
- Change the time bucketing granularity (day to week)
- Add or remove filters
- Change the metric aggregation (e.g., from avg to p95)
- Update the name or description
- Switch the view (e.g., from OBSERVATIONS to TRACES)
- Change the dimension field

Accept one or more changes in a single interaction. Do not require the user to
re-specify unchanged fields.

### 4. Validate the Updated Configuration

Before applying, validate the complete updated configuration against
`skills/create-widget/references/widget-schema-reference.md`:

- Confirm `view` is a valid `DashboardWidgetViews` enum value.
- Confirm `chart_type` is a valid `DashboardWidgetChartType` enum value.
- Confirm each dimension field is valid for the chosen view.
- Confirm each metric field and aggregation is valid for the chosen view.
- Confirm `chart_config` shape matches the chosen `chart_type`.

If the user changes the `view`, verify that the existing dimensions and metrics
are still valid for the new view. If not, inform the user which fields need to
be updated and suggest replacements.

### 5. Apply the UPDATE

Use psycopg2 with parameterized queries:

```sql
UPDATE dashboard_widgets
SET name = %(name)s,
    description = %(description)s,
    view = %(view)s,
    dimensions = %(dimensions)s::jsonb,
    metrics = %(metrics)s::jsonb,
    filters = %(filters)s::jsonb,
    chart_type = %(chart_type)s,
    chart_config = %(chart_config)s::jsonb,
    updated_at = NOW()
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

Pass all values as parameters. Serialize JSON columns via `json.dumps()` and
cast to `::jsonb` in the query.

**Fallback** -- if psycopg2 is unavailable, use docker exec psql:

```bash
docker exec -i <container_name> psql -U <user> -d <dbname> -c "UPDATE ..."
```

### 6. Verify the Update

After the UPDATE, read the widget back to confirm changes took effect:

```sql
SELECT id, name, description, view, chart_type, dimensions, metrics,
       filters, chart_config, updated_at
FROM dashboard_widgets
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

Present the updated configuration to the user for final confirmation.

### 7. Report Affected Dashboards

Check which dashboards reference this widget:

```sql
SELECT id, name FROM dashboards
WHERE project_id = %(project_id)s
  AND definition::text LIKE %(widget_id_pattern)s;
```

Inform the user which dashboards will reflect the updated widget configuration.

## Error Handling

- If no widget matches the provided ID, report this and suggest using
  `list-widgets` to find the correct widget.
- If the UPDATE affects 0 rows (e.g., wrong project_id), report that no widget
  was updated and verify the project ID.
- If the database connection fails, attempt the docker exec psql fallback
  before reporting failure.

## Reference

For schema details, use `skills/create-widget/references/widget-schema-reference.md`.
