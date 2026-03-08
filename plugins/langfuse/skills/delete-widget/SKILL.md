---
name: delete-widget
description: >
  This skill should be used when the user wants to delete or remove a Langfuse
  dashboard widget. Trigger phrases include "delete widget", "remove widget",
  "drop widget". It performs referential integrity checks against dashboards
  before deletion and cleans up dashboard references.
---

# Delete Langfuse Dashboard Widget

Delete a Langfuse dashboard widget from PostgreSQL with full referential
integrity checks. Before removing the widget row, inspect all dashboards that
reference it, warn the user, clean up references, and only then perform the
deletion.

## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python library `psycopg2-binary` installed. If missing, install via
  `uv add psycopg2-binary`.
- The widget ID to delete. If unknown, ask the user or use the `list-widgets`
  skill to enumerate available widgets.

## Step-by-Step Procedure

### 1. Identify the Target Widget

Accept the widget ID from the user. Verify it exists:

```sql
SELECT id, name, description, view, chart_type, created_at
FROM dashboard_widgets
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

If no row is returned, inform the user that the widget does not exist and
suggest using `list-widgets` to find the correct ID.

Display the widget details so the user can confirm they are deleting the
correct widget.

### 2. Check Dashboard References

Query all dashboards in the project for references to this widget:

```sql
SELECT id, name, definition
FROM dashboards
WHERE project_id = %(project_id)s
  AND definition::text LIKE %(widget_id_pattern)s;
```

Where `%(widget_id_pattern)s` is `%<WIDGET_ID>%` (percent-wrapped widget ID
for LIKE matching).

### 3. Handle Referenced Widgets

**If the widget is referenced by one or more dashboards:**

Present a warning listing each dashboard that contains this widget:

```
WARNING: This widget is referenced by the following dashboards:
  - "Dashboard Name A" (id: <dashboard_id_a>)
  - "Dashboard Name B" (id: <dashboard_id_b>)

Deleting this widget will remove it from these dashboards.
Proceed? (yes/no)
```

Wait for explicit user confirmation before proceeding.

**If the widget is not referenced by any dashboard:**

Still ask for confirmation:

```
Widget "<widget_name>" (id: <widget_id>) is not on any dashboard.
Delete permanently? (yes/no)
```

### 4. Remove Widget References from Dashboards

If the widget is referenced by dashboards and the user confirmed deletion,
clean up each dashboard's `definition.widgets[]` array.

For each affected dashboard:

1. Parse the `definition` JSON.
2. Remove any entry from the `widgets` array where `widgetId` matches the
   target widget ID.
3. Serialize the updated definition back to JSON.
4. UPDATE the dashboard:

```sql
UPDATE dashboards
SET definition = %(updated_definition)s::jsonb,
    updated_at = NOW()
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

Repeat for every affected dashboard. Use a transaction if possible (psycopg2
connection with `autocommit=False`) to ensure atomicity.

### 5. Delete the Widget Row

After all dashboard references have been cleaned up, delete the widget:

```sql
DELETE FROM dashboard_widgets
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

### 6. Verify Deletion

Confirm the widget no longer exists:

```sql
SELECT COUNT(*) FROM dashboard_widgets
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

The count should be 0. Report success to the user.

Also verify that dashboard references were cleaned up:

```sql
SELECT id, name FROM dashboards
WHERE project_id = %(project_id)s
  AND definition::text LIKE %(widget_id_pattern)s;
```

This should return no rows.

### 7. Report Summary

Present a summary of actions taken:

- Widget deleted: name, ID
- Dashboards cleaned up: list of dashboard names and IDs (if any)
- Timestamp of deletion

## Transaction Safety

When using psycopg2, wrap the entire operation (dashboard updates + widget
deletion) in a single transaction:

```python
conn.autocommit = False
try:
    with conn.cursor() as cur:
        # Update each affected dashboard
        for dashboard in affected_dashboards:
            cur.execute(update_dashboard_sql, params)
        # Delete the widget
        cur.execute(delete_widget_sql, params)
    conn.commit()
except Exception:
    conn.rollback()
    raise
```

This ensures that if any step fails, no partial changes are left behind.

## Error Handling

- If the widget does not exist, report this and do not attempt deletion.
- If the user declines confirmation, abort the operation entirely.
- If the dashboard definition JSON is malformed, report the specific dashboard
  and skip its cleanup, warning the user of the inconsistency.
- If the DELETE affects 0 rows despite earlier SELECT finding the widget,
  report a potential concurrent modification.
- If the database connection fails, attempt the docker exec psql fallback
  before reporting failure.
