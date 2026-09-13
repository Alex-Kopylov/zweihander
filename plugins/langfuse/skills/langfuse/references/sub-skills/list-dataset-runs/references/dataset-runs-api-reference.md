# Dataset Runs API Reference

Complete reference for browsing Langfuse dataset runs and run items.

## REST API Endpoints

### List Runs for a Dataset

```
GET /api/public/datasets/{datasetName}/runs
```

**Query Parameters:**
- `page` (int, default: 1)
- `limit` (int, default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "4dab899b-dc34-44c4-8a58-3c7eba4f06a0",
      "name": "html-controls-default-20260227T1759",
      "description": null,
      "metadata": {
        "model": "gpt-4o",
        "provider": "azure",
        "prompt_id": "5f135f85-...",
        "experiment_name": "..."
      },
      "datasetId": "cmkqphpqm001mml076oztd8mk",
      "createdAt": "2026-02-27T17:59:18.556Z",
      "updatedAt": "2026-02-27T17:59:18.556Z",
      "datasetName": "test"
    }
  ],
  "meta": { "page": 1, "limit": 50, "totalItems": 7, "totalPages": 1 }
}
```

Note: Run `metadata` may contain experiment configuration (model, provider, parameters) depending on how the experiment was triggered.

### Get Run Items

```
GET /api/public/dataset-run-items?runName={runName}&datasetId={datasetId}&limit=50&page=1
```

**Query Parameters:**

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `runName` | string | Yes | The dataset run name |
| `datasetId` | string | Yes | The dataset ID |
| `limit` | int | No | Default: 50 |
| `page` | int | No | Default: 1 |

**Response:**
```json
{
  "data": [
    {
      "id": "500c7d0f-bd86-4861-991d-55553a10895a",
      "traceId": "22fcdb07add3f554c43605d01da48e8f",
      "observationId": null,
      "datasetRunId": "4dab899b-dc34-44c4-8a58-3c7eba4f06a0",
      "datasetRunName": "html-controls-default-20260227T1759",
      "datasetItemId": "527d4aa8-ba0e-46c9-aaab-ad3333500703",
      "createdAt": "2026-02-27T17:59:31.811Z",
      "updatedAt": "2026-02-27T17:59:31.811Z"
    }
  ],
  "meta": { "page": 1, "limit": 50, "totalItems": 2, "totalPages": 1 }
}
```

**Key field:** `traceId` links each run item to its execution trace for scores and details.

## Database Schema

### `dataset_runs` Table

| Column | Type | PK | Notes |
|--------|------|----|-------|
| `id` | text | Yes (composite with project_id) | UUID v4 or CUID |
| `name` | text | | Run name (unique per dataset) |
| `dataset_id` | text | | FK to datasets |
| `project_id` | text | Yes (composite with id) | |
| `description` | text | | Optional |
| `metadata` | jsonb | | Experiment config, model info, etc. |
| `created_at` | timestamp(3) | | |
| `updated_at` | timestamp(3) | | |

**Unique Constraint:** `(dataset_id, project_id, name)`

### `dataset_run_items` — ClickHouse

`dataset_run_items` data lives in ClickHouse (`dataset_run_items_rmt`, denormalized with inline item/run data); the Postgres table exists but is empty. Use the REST API or direct ClickHouse queries.

| Column | Type | Notes |
|--------|------|-------|
| `id` | String | Run item ID |
| `project_id` | String | |
| `dataset_run_id` | String | |
| `dataset_item_id` | String | |
| `dataset_id` | String | |
| `trace_id` | String | Linked trace |
| `observation_id` | Nullable(String) | |
| `dataset_run_name` | String | Inline copy |
| `dataset_run_metadata` | Map(String, String) | Inline copy |
| `dataset_item_input` | Nullable(String) | Inline copy (ZSTD compressed) |
| `dataset_item_expected_output` | Nullable(String) | Inline copy |

## Common Queries

### Runs with item count (via REST API — preferred)
```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets/{NAME}/runs"
```

Then for each run, get item count:
```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-run-items?runName={RUN_NAME}&datasetId={DATASET_ID}&limit=1"
```
Check `meta.totalItems` in the response for the count.

### Run items with trace details (ClickHouse)
```sql
SELECT dri.id, dri.dataset_item_id, dri.trace_id,
       t.name AS trace_name, t.input AS trace_input, t.output AS trace_output,
       dri.created_at
FROM dataset_run_items_rmt dri
LEFT JOIN traces t ON dri.trace_id = t.id AND dri.project_id = t.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
ORDER BY dri.created_at;
```

Run via: `docker exec langfuse-clickhouse clickhouse-client --query "..."`.

### Run items with scores (ClickHouse)
```sql
SELECT dri.dataset_item_id, dri.trace_id,
       s.name AS score_name, s.value, s.data_type, s.source,
       s.comment
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
ORDER BY dri.dataset_item_id, s.name;
```

### Aggregate scores per run (ClickHouse)
```sql
SELECT s.name AS score_name,
       COUNT(*) AS count,
       AVG(s.value) AS avg_score,
       MIN(s.value) AS min_score,
       MAX(s.value) AS max_score,
       stddevPop(s.value) AS stddev
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
  AND s.data_type = 'NUMERIC'
GROUP BY s.name
ORDER BY s.name;
```
