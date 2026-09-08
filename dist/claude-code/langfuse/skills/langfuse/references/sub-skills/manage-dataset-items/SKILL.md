---
name: manage-dataset-items
description: >-
  This skill should be used when the user wants to create, update, archive, delete, list, or bulk-populate
  dataset items in Langfuse. Trigger phrases include "add items", "create item", "populate dataset",
  "update item", "archive item", "delete item", "bulk import", "add test cases".
---

Manage dataset items: create, upsert, archive, browse, and bulk-populate.

## Create Items

### Single Item via API

```bash
curl -s -X POST \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-items" \
  -H "Content-Type: application/json" \
  -d '{
    "datasetName": "{dataset_name}",
    "input": { ... },
    "expectedOutput": { ... },
    "metadata": { "source": "manual" }
  }'
```

Key fields:
- `datasetName` (required) — target dataset
- `input` (any JSON) — item input data
- `expectedOutput` (any JSON, optional) — for evaluation comparison
- `metadata` (object, optional) — arbitrary metadata
- `id` (string, optional) — provide to upsert an existing item
- `sourceTraceId` (string, optional) — link to originating trace
- `sourceObservationId` (string, optional) — link to originating observation

### Upsert (Update Existing Item)

Pass the existing `id` to update. This creates a **new version** (the old version is preserved with `valid_to` set).

```bash
curl -s -X POST \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-items" \
  -H "Content-Type: application/json" \
  -d '{
    "datasetName": "{dataset_name}",
    "id": "{existing_item_id}",
    "input": { ... },
    "expectedOutput": { ... }
  }'
```

### Bulk Create via Python Script

For many items, use Python with the REST API:

```python
import json
import httpx

client = httpx.Client(
    base_url="{HOST}/api/public",
    auth=("{PUBLIC_KEY}", "{SECRET_KEY}"),
    timeout=30,
)

items = [
    {"input": {...}, "expectedOutput": {...}, "metadata": {...}},
    # ... more items
]

for item in items:
    response = client.post(
        "/dataset-items",
        json={"datasetName": "{dataset_name}", **item},
    )
    response.raise_for_status()
    print(f"Created item: {response.json()['id']}")
```

## Create Items from Traces

To populate a dataset from production traces:

1. **Discover traces** using the `discover-traces` skill to identify relevant trace names/tags.
2. **Fetch traces** via API:
   ```bash
   curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
     "$HOST/api/public/traces?name={trace_name}&limit=10"
   ```
3. **Extract input/output** from each trace.
4. **Create items** linking back to the source:
   ```json
   {
     "datasetName": "{dataset_name}",
     "input": { "extracted from trace input" },
     "expectedOutput": { "extracted from trace output or null" },
     "sourceTraceId": "{trace_id}",
     "metadata": { "source": "trace", "trace_name": "{name}" }
   }
   ```

## Archive Items

Archive an item (keeps it but excludes from active experiments):

```bash
curl -s -X POST \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-items" \
  -H "Content-Type: application/json" \
  -d '{
    "datasetName": "{dataset_name}",
    "id": "{item_id}",
    "status": "ARCHIVED"
  }'
```

## Hard Delete Items (DB Only)

The REST API does not support hard deletion. Use direct DB access:

```sql
UPDATE dataset_items
SET is_deleted = true, valid_to = CURRENT_TIMESTAMP
WHERE project_id = '{PROJECT_ID}'
  AND id = '{ITEM_ID}'
  AND valid_to IS NULL;
```

**Warning:** Hard deletion cannot be undone. Always confirm with the user before executing.

## Browse Items

List items with pagination:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-items?datasetName={name}&limit=50&page=1"
```

Or get all items inline with the dataset:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/datasets/{name}"
```

## Verification

After create/update, fetch the item:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-items?datasetName={name}&limit=50"
```

Check that:
- Item count matches expectations
- Input data is correct
- Status is `ACTIVE` (not accidentally archived)

Refer to `references/dataset-items-api-reference.md` for complete field details and schema validation behavior.
