---
name: layout-widgets
description: >
  This skill should be used when the user needs to calculate grid positions for
  widget placement on a Langfuse dashboard. Trigger phrases include "layout
  widgets", "widget placement", "grid position", "arrange widgets", "widget
  positioning". It computes x/y coordinates and sizes for placing widgets on
  the 12-column dashboard grid.
---

# Layout Widgets on Langfuse Dashboard Grid

Calculate grid positions for placing widgets on a Langfuse dashboard. The
Langfuse dashboard uses a 12-column grid system. This skill determines the
correct `x`, `y`, `x_size`, and `y_size` values for new widget placement
entries.

## Grid Rules

- The dashboard grid is **12 columns wide** (Langfuse default).
- Maximum **2 half-width widgets per row** (each 6 columns).
- Default widget size: `x_size: 6, y_size: 4` (half-width, 4 rows tall).
- Full-width widget: `x_size: 12, y_size: 4`.
- Widgets cannot overlap.
- Column positions: 0 through 11 (zero-indexed).

## Widget Placement Entry Shape

Each widget placement entry in the dashboard `definition.widgets[]` array:

```json
{
  "type": "widget",
  "id": "<uuid4 for placement slot>",
  "widgetId": "<cuid of dashboard_widget row>",
  "x": 0,
  "y": 0,
  "x_size": 6,
  "y_size": 4
}
```

Key distinction:
- **`id`** -- UUID v4 identifying this specific placement slot on the dashboard.
  Generated via `uuid.uuid4()`.
- **`widgetId`** -- CUID referencing the `dashboard_widgets.id` row. This is the
  widget's data identity.

## Placement Algorithm

### Step 1: Parse Existing Widget Positions

Read the current dashboard definition:

```sql
SELECT definition FROM dashboards
WHERE id = %(dashboard_id)s AND project_id = %(project_id)s;
```

Extract all widget placement entries from `definition["widgets"]`. Each entry
has `x`, `y`, `x_size`, and `y_size`.

### Step 2: Find the Bottom of the Grid

Calculate the maximum occupied Y position:

```python
if not existing_widgets:
    max_y = 0
else:
    max_y = max(w["y"] + w["y_size"] for w in existing_widgets)
```

### Step 3: Analyze the Last Row

Find all widgets whose `y` position equals the start of the last row:

```python
last_row_y = max(w["y"] for w in existing_widgets) if existing_widgets else 0
last_row_widgets = [w for w in existing_widgets if w["y"] == last_row_y]
```

Calculate the total width consumed on the last row:

```python
last_row_width = sum(w["x_size"] for w in last_row_widgets)
```

### Step 4: Determine New Widget Position

Apply the placement rules:

```python
def calculate_position(
    existing_widgets: list[dict],
    new_x_size: int = 6,
    new_y_size: int = 4,
) -> dict:
    """Calculate the grid position for a new widget."""
    if not existing_widgets:
        return {"x": 0, "y": 0, "x_size": new_x_size, "y_size": new_y_size}

    max_y = max(w["y"] + w["y_size"] for w in existing_widgets)
    last_row_y = max(w["y"] for w in existing_widgets)
    last_row_widgets = [w for w in existing_widgets if w["y"] == last_row_y]
    last_row_width = sum(w["x_size"] for w in last_row_widgets)

    # Check if there is room on the last row
    remaining_space = 12 - last_row_width
    if remaining_space >= new_x_size and len(last_row_widgets) < 2:
        # Place beside the existing widget on the last row
        new_x = last_row_width
        new_y = last_row_y
    else:
        # Start a new row below all existing content
        new_x = 0
        new_y = max_y

    return {"x": new_x, "y": new_y, "x_size": new_x_size, "y_size": new_y_size}
```

### Step 5: Construct the Placement Entry

Generate a UUID v4 for the placement slot and build the entry:

```python
import uuid

placement = calculate_position(existing_widgets)
entry = {
    "type": "widget",
    "id": str(uuid.uuid4()),
    "widgetId": widget_id,  # CUID from dashboard_widgets.id
    **placement,
}
```

## Layout Examples

### Empty Dashboard -- First Widget

Position: `x=0, y=0, x_size=6, y_size=4`

```
|  Widget A (6 cols)  |                     |
|                     |                     |
```

### One Half-Width Widget -- Second Widget

Position: `x=6, y=0, x_size=6, y_size=4`

```
|  Widget A (6 cols)  |  Widget B (6 cols)  |
|                     |                     |
```

### Two Half-Width Widgets -- Third Widget (New Row)

Position: `x=0, y=4, x_size=6, y_size=4`

```
|  Widget A (6 cols)  |  Widget B (6 cols)  |
|                     |                     |
|  Widget C (6 cols)  |                     |
|                     |                     |
```

### Full-Width Widget on Last Row -- Next Widget (New Row)

When the last row has a full-width widget (`x_size=12`), always start a new row:

Position: `x=0, y=8, x_size=6, y_size=4`

```
|        Full-Width Widget (12 cols)        |
|                                           |
|  Widget D (6 cols)  |                     |
|                     |                     |
```

## Batch Layout

When placing multiple widgets at once (e.g., from `suggest-widgets`), call
`calculate_position` iteratively, appending each new placement entry to the
`existing_widgets` list before calculating the next position:

```python
new_entries = []
all_widgets = list(existing_widgets)  # copy

for widget_id in widget_ids_to_place:
    position = calculate_position(all_widgets)
    entry = {
        "type": "widget",
        "id": str(uuid.uuid4()),
        "widgetId": widget_id,
        **position,
    }
    new_entries.append(entry)
    all_widgets.append(entry)  # include in calculations for next widget
```

## Size Recommendations

| Widget Type        | Recommended Size         |
|--------------------|--------------------------|
| Number (big stat)  | `x_size: 3, y_size: 2`  |
| Standard chart     | `x_size: 6, y_size: 4`  |
| Wide chart         | `x_size: 12, y_size: 4` |
| Tall pivot table   | `x_size: 12, y_size: 6` |
| Histogram          | `x_size: 6, y_size: 4`  |

Adjust sizes based on the user's preference. The algorithm handles any valid
size within the 12-column constraint.
