# Datasets API Reference



## REST API Endpoints

All endpoints use HTTP Basic Auth: `curl -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/..."`.

### List All Datasets

```
GET /api/public/datasets
```

**Query Parameters:**
- `page` (int, default: 1) — Page number
- `limit` (int, default: 50) — Items per page

**Response:**
```json
{
  "data": [
    {
      "id": "cmkqphpqm001mml076oztd8mk",
      "name": "test",
      "description": null,
      "metadata": null,
      "inputSchema": null,
      "expectedOutputSchema": null,
      "projectId": "local-dev-project",
      "createdAt": "2026-01-23T09:56:34.318Z",
      "updatedAt": "2026-02-27T16:30:55.254Z",
      "items": ["527d4aa8-ba0e-46c9-aaab-ad3333500703", "66ee0b10-9800-431b-adb1-9484bb10ee61"],
      "runs": ["html-controls-default-20260227T1759", "html-controls-default-20260227T1745"]
    }
  ],
  "meta": { "page": 1, "limit": 50, "totalItems": 3, "totalPages": 1 }
}
```

Note: `items` are IDs and `runs` are names; use the single-dataset endpoint for full details.

### List All Datasets (v2)

```
GET /api/public/v2/datasets
```

Same query parameters; similar response, but no inline `items[]` or `runs[]`.

### Get Single Dataset

```
GET /api/public/datasets/{name}
```

Returns the dataset with **full item objects** and run names. URL-encode the name if it contains slashes.

**Response includes:**
- Full dataset metadata
- `items[]` — array of complete item objects (`id`, `input`, `expectedOutput`, `metadata`, `status`, `sourceTraceId`, `sourceObservationId`, `datasetName`)
- `runs[]` — array of run name strings

### Create Dataset

```
POST /api/public/datasets
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "my-dataset",
  "description": "Optional description",
  "metadata": { "key": "value" },
  "inputSchema": { "type": "object", "properties": { ... } },
  "expectedOutputSchema": { "type": "object", "properties": { ... } }
}
```

- `name` (required) — must be unique per project. Use `/` for folder structure (e.g., `benchmarks/ssp-controls`).
- `description`, `metadata`, `inputSchema`, `expectedOutputSchema` — all optional.
- `inputSchema` and `expectedOutputSchema` are JSON Schema objects for validation.

**Upsert behavior:** If the name already exists, it updates that dataset's description, metadata, and schemas.

### List Dataset Items

```
GET /api/public/dataset-items?datasetName={name}&limit=50&page=1
```

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

### Create / Upsert Dataset Item

```
POST /api/public/dataset-items
Content-Type: application/json
```

**Request Body:**
```json
{
  "datasetName": "my-dataset",
  "input": { ... },
  "expectedOutput": { ... },
  "metadata": { "source": "manual" },
  "id": "optional-existing-id-for-upsert",
  "sourceTraceId": "optional-trace-id",
  "sourceObservationId": "optional-observation-id",
  "status": "ACTIVE"
}
```

- `datasetName` (required) — target dataset
- `input` — the item's input data (any JSON)
- `expectedOutput` — optional expected output for evaluation
- `id` — if provided and exists, upserts (creates new version). If absent, auto-generates.
- `status` — `ACTIVE` (default) or `ARCHIVED`
- `sourceTraceId` / `sourceObservationId` — link item to a production trace/observation

## Database Schema

### `datasets` Table

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'datasets'
ORDER BY ordinal_position;
```

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | text | NOT NULL | CUID format, part of PK |
| `name` | text | NOT NULL | Unique per project |
| `project_id` | text | NOT NULL | FK to projects, part of PK |
| `created_at` | timestamp(3) | NOT NULL | Default: `CURRENT_TIMESTAMP` |
| `updated_at` | timestamp(3) | NOT NULL | Default: `CURRENT_TIMESTAMP` |
| `description` | text | NULL | |
| `metadata` | jsonb | NULL | |
| `remote_experiment_payload` | jsonb | NULL | Default webhook payload |
| `remote_experiment_url` | text | NULL | Webhook URL for Custom Experiment |
| `expected_output_schema` | json | NULL | JSON Schema for item expected outputs |
| `input_schema` | json | NULL | JSON Schema for item inputs |

**Primary Key:** `(id, project_id)`
**Unique Constraint:** `(project_id, name)`

### `dataset_items` Table

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | text | NOT NULL | Item ID (versioned — same ID across versions) |
| `input` | jsonb | NULL | Item input data |
| `expected_output` | jsonb | NULL | Expected output |
| `source_observation_id` | text | NULL | Link to observation |
| `dataset_id` | text | NOT NULL | FK to datasets |
| `created_at` | timestamp(3) | NOT NULL | |
| `updated_at` | timestamp(3) | NOT NULL | |
| `status` | DatasetStatus | NULL | `ACTIVE` or `ARCHIVED` (default: `ACTIVE`) |
| `source_trace_id` | text | NULL | Link to trace |
| `metadata` | jsonb | NULL | |
| `project_id` | text | NOT NULL | |
| `is_deleted` | boolean | NOT NULL | Default: `false` (soft delete) |
| `valid_from` | timestamp(3) | NOT NULL | Version start (default: `CURRENT_TIMESTAMP`) |
| `valid_to` | timestamp(3) | NULL | Version end (`NULL` = current version) |

**Primary Key:** `(id, project_id, valid_from)`

**Versioning:** Each item update creates a new row. Query current versions with `WHERE valid_to IS NULL AND is_deleted = false`.

## Fields NOT Available via REST API

These fields require direct database access:

| Field | Table | Notes |
|-------|-------|-------|
| `remote_experiment_url` | `datasets` | Webhook URL for Custom Experiment |
| `remote_experiment_payload` | `datasets` | Default payload for webhook |
| `is_deleted` | `dataset_items` | Soft delete flag |
| `valid_from` / `valid_to` | `dataset_items` | Version timestamps |

## Common DB Queries

### Count items per dataset
```sql
SELECT d.name, COUNT(di.id) AS item_count
FROM datasets d
LEFT JOIN dataset_items di ON d.id = di.dataset_id
  AND di.project_id = d.project_id
  AND di.valid_to IS NULL
  AND di.is_deleted = false
WHERE d.project_id = '{PROJECT_ID}'
GROUP BY d.name
ORDER BY d.name;
```

### Get current (non-deleted) items for a dataset
```sql
SELECT id, input, expected_output, metadata, status,
       source_trace_id, created_at, updated_at
FROM dataset_items
WHERE project_id = '{PROJECT_ID}'
  AND dataset_id = '{DATASET_ID}'
  AND valid_to IS NULL
  AND is_deleted = false
ORDER BY created_at;
```

### Check if remote experiment is configured
```sql
SELECT name, remote_experiment_url, remote_experiment_payload
FROM datasets
WHERE project_id = '{PROJECT_ID}'
  AND remote_experiment_url IS NOT NULL;
```
