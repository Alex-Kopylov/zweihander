# Dataset Items API Reference

Complete reference for Langfuse dataset item management.

## REST API

### Create / Upsert Item

```
POST /api/public/dataset-items
Content-Type: application/json
```

**Request Fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `datasetName` | string | Yes | Target dataset name |
| `input` | any | No | Item input data (JSON) |
| `expectedOutput` | any | No | Expected output for comparison |
| `metadata` | object | No | Arbitrary metadata |
| `id` | string | No | Provide existing ID to upsert (creates new version) |
| `sourceTraceId` | string | No | Link to originating trace |
| `sourceObservationId` | string | No | Link to originating observation |
| `status` | string | No | `ACTIVE` (default) or `ARCHIVED` |

**Upsert Behavior:**
- If `id` is not provided: creates new item with auto-generated ID.
- If `id` is provided and exists: creates a new version. The previous version's `valid_to` is set. The new version has `valid_from = NOW()` and `valid_to = NULL`.
- If `id` is provided and does not exist: creates new item with the given ID.

**Schema Validation:**
- If the parent dataset has `inputSchema` set, the `input` field is validated against it.
- If validation fails, the item creation is rejected with error details.
- Same applies for `expectedOutputSchema` against `expectedOutput`.

### List Items

```
GET /api/public/dataset-items?datasetName={name}&limit=50&page=1
```

**Query Parameters:**

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `datasetName` | string | required | Filter by dataset name |
| `limit` | int | 50 | Items per page |
| `page` | int | 1 | Page number |

**Response:**
```json
{
  "data": [
    {
      "id": "527d4aa8-ba0e-46c9-aaab-ad3333500703",
      "datasetId": "cmkqphpqm001mml076oztd8mk",
      "input": { ... },
      "expectedOutput": null,
      "metadata": null,
      "status": "ACTIVE",
      "sourceTraceId": null,
      "sourceObservationId": null,
      "createdAt": "2026-02-27T09:53:21.144Z",
      "updatedAt": "2026-02-27T09:53:21.144Z",
      "datasetName": "test"
    }
  ],
  "meta": { "page": 1, "limit": 50, "totalItems": 2, "totalPages": 1 }
}
```

Note: The API returns only the **current version** of each item (i.e., `valid_to IS NULL`). Historical versions require direct DB access.

## Database Schema

### `dataset_items` Table

| Column | Type | PK | Notes |
|--------|------|----|-------|
| `id` | text | Yes (composite) | Item ID — same across versions |
| `project_id` | text | Yes (composite) | |
| `valid_from` | timestamp(3) | Yes (composite) | Version start time |
| `input` | jsonb | | Item input data |
| `expected_output` | jsonb | | Expected output |
| `dataset_id` | text | | FK to datasets |
| `status` | DatasetStatus | | `ACTIVE` or `ARCHIVED` |
| `source_trace_id` | text | | Link to trace |
| `source_observation_id` | text | | Link to observation |
| `metadata` | jsonb | | |
| `is_deleted` | boolean | | Soft delete (default: `false`) |
| `valid_to` | timestamp(3) | | Version end (`NULL` = current) |

### Versioning Model

Items use a temporal versioning pattern:

```
Version 1: valid_from=T1, valid_to=T2  (superseded)
Version 2: valid_from=T2, valid_to=T3  (superseded)
Version 3: valid_from=T3, valid_to=NULL (current)
```

**Current versions only:**
```sql
WHERE valid_to IS NULL AND is_deleted = false
```

**All versions of an item:**
```sql
WHERE id = '{ITEM_ID}' AND project_id = '{PROJECT_ID}'
ORDER BY valid_from DESC
```

**Dataset version at a point in time:**
```sql
WHERE dataset_id = '{DATASET_ID}'
  AND project_id = '{PROJECT_ID}'
  AND valid_from <= '{TIMESTAMP}'
  AND (valid_to IS NULL OR valid_to > '{TIMESTAMP}')
  AND is_deleted = false
```

## Operations NOT Available via API

| Operation | How to Accomplish |
|-----------|-------------------|
| Hard delete an item | `UPDATE dataset_items SET is_deleted = true, valid_to = CURRENT_TIMESTAMP WHERE id = '{ID}' AND valid_to IS NULL` |
| View item version history | Query all rows with same `id`, ordered by `valid_from DESC` |
| Restore a deleted item | `UPDATE dataset_items SET is_deleted = false WHERE id = '{ID}' AND valid_from = '{VERSION_VALID_FROM}'` |
| Query items at a past point in time | Use `valid_from`/`valid_to` temporal query (see above) |
| Bulk delete items | `UPDATE dataset_items SET is_deleted = true, valid_to = CURRENT_TIMESTAMP WHERE dataset_id = '{DATASET_ID}' AND valid_to IS NULL` |
