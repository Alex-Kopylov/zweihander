---
name: manage-dashboard
description: >
  This skill should be used when the user wants to perform CRUD operations on
  Langfuse dashboards. Trigger phrases include "create dashboard", "list
  dashboards", "manage dashboards", "delete dashboard", "add widget to
  dashboard", "remove widget from dashboard". It handles listing, creating,
  updating metadata, deleting dashboards, and managing widget placement entries
  within dashboard definitions.
---

# Manage Langfuse Dashboards

Perform create, read, update, and delete operations on Langfuse dashboards,
including managing the widget placement entries within each dashboard's
`definition` JSON column.

## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python libraries `cuid2` and `psycopg2-binary` installed. If missing, install
  via `uv add cuid2 psycopg2-binary`.

## Operations

### List Dashboards

Query all dashboards for the current project:

```sql
SELECT id, name, description, created_at, updated_at,
       jsonb_array_length(definition->'widgets') AS widget_count
FROM dashboards
WHERE project_id = %(project_id)s
ORDER BY updated_at DESC;
```

Present the results as a table with columns: Name, Widget Count, Created,
Last Updated, ID. If no dashboards exist, inform the user and offer to create
one.

### Create Dashboard

Generate a CUID for the new dashboard ID:

```python
from cuid2 import cuid_wrapper

cuid_generator = cuid_wrapper()
dashboard_id = cuid_generator()
```

Ask the user for a name and optional description. Insert the dashboard with an
empty widget list:

```sql
INSERT INTO dashboards (
  id, created_at, updated_at, created_by, updated_by,
  project_id, name, description, definition, filters
) VALUES (
  %(id)s, NOW(), NOW(), NULL, NULL,
  %(project_id)s, %(name)s, %(description)s,
  '{"widgets": []}'::jsonb, '[]'::jsonb
);
```

After creation, provide the dashboard URL:

```
{LANGFUSE_HOST}/project/{PROJECT_ID}/dashboards/{DASHBOARD_ID}
```

### Update Dashboard Metadata

Update the name and/or description of an existing dashboard:

```sql
UPDATE dashboards
SET name = %(name)s,
    description = %(description)s,
    updated_at = NOW()
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

Only update the fields the user wants to change. For unchanged fields, use the
current values from the database.

### Delete Dashboard

Before deleting, check whether the dashboard contains widgets:

```sql
SELECT name, definition
FROM dashboards
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

Parse the `definition` JSON and check the `widgets` array length.

**If the dashboard has widgets:**

Warn the user that the dashboard contains widget placement entries. Deleting
the dashboard will orphan these placement entries but will NOT delete the
underlying `dashboard_widgets` rows. Ask for explicit confirmation:

```
WARNING: Dashboard "<name>" contains <N> widget placements.
The widgets themselves will NOT be deleted, only their placement on this dashboard.
Proceed with deletion? (yes/no)
```

**If the dashboard is empty or the user confirms:**

```sql
DELETE FROM dashboards
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

Verify deletion:

```sql
SELECT COUNT(*) FROM dashboards
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

### Add Widget to Dashboard

Add a widget placement entry to an existing dashboard's `definition.widgets[]`
array. Delegate grid position calculation to the `layout-widgets` skill.

1. Verify the widget exists in `dashboard_widgets`:

```sql
SELECT id, name FROM dashboard_widgets
WHERE id = %(widget_id)s AND project_id = %(project_id)s;
```

2. Read the current dashboard definition:

```sql
SELECT definition FROM dashboards
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

3. Use the `layout-widgets` skill to calculate the placement position (x, y,
   x_size, y_size) based on existing widget positions.

4. Generate a UUID v4 for the placement slot ID:

```python
import uuid
placement_id = str(uuid.uuid4())
```

5. Construct the placement entry:

```json
{
  "type": "widget",
  "id": "<uuid4>",
  "widgetId": "<cuid of dashboard_widget>",
  "x": 0,
  "y": 0,
  "x_size": 6,
  "y_size": 4
}
```

6. Append to the `widgets` array and update:

```sql
UPDATE dashboards
SET definition = %(updated_definition)s::jsonb,
    updated_at = NOW()
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

### Remove Widget from Dashboard

Remove a widget placement entry from a dashboard without deleting the
underlying `dashboard_widgets` row.

1. Read the current dashboard definition:

```sql
SELECT definition FROM dashboards
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

2. Parse the `definition` JSON.

3. Find the placement entry where `widgetId` matches the target widget ID.
   If not found, inform the user that the widget is not on this dashboard.

4. Remove the matching entry from the `widgets` array.

5. Optionally re-compact the grid positions to remove gaps. This is a
   convenience step; skipping it leaves visual gaps on the dashboard but does
   not break functionality.

6. Update the dashboard definition:

```sql
UPDATE dashboards
SET definition = %(updated_definition)s::jsonb,
    updated_at = NOW()
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

## Error Handling

- If a dashboard ID does not exist, report this and suggest listing dashboards.
- If a widget ID does not exist when adding to a dashboard, report this and
  suggest using `list-widgets` to find valid widget IDs.
- If the dashboard definition JSON is malformed, report the structure issue
  and do not attempt partial updates.
- If the database connection fails, attempt the docker exec psql fallback
  before reporting failure.

## Related Skills

- `create-widget` -- create new widgets to add to dashboards.
- `layout-widgets` -- calculate grid positions for widget placement.
- `delete-widget` -- delete widgets (also cleans up dashboard references).
