---
name: list-dataset-runs
description: >-
  Use when the user wants to list dataset runs, browse experiment runs,
  see what experiments have been executed, check run status, or inspect run metadata.
  Trigger phrases include "list runs", "show runs", "experiment runs", "dataset runs",
  "what experiments have been run", "browse runs".
---

List and browse dataset runs (experiment executions) for a Langfuse dataset.

## Step 1: Identify the Dataset

If the user specifies a dataset name, use it directly. Otherwise, use `discover-datasets` to list available datasets and let the user choose.

## Step 2: List Runs via API

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/datasets/{DATASET_NAME}/runs"
```

**Response:**
```json
{
  "data": [
    {
      "id": "4dab899b-dc34-44c4-8a58-3c7eba4f06a0",
      "name": "html-controls-default-20260227T1759",
      "description": null,
      "metadata": {},
      "datasetId": "cmkqphpqm001mml076oztd8mk",
      "createdAt": "2026-02-27T17:59:18.556Z",
      "updatedAt": "2026-02-27T17:59:18.556Z",
      "datasetName": "test"
    }
  ],
  "meta": { "page": 1, "limit": 50, "totalItems": 7, "totalPages": 1 }
}
```

If API is unavailable, fall back to DB:

```sql
SELECT id, name, description, metadata, created_at, updated_at
FROM dataset_runs
WHERE project_id = '{PROJECT_ID}'
  AND dataset_id = '{DATASET_ID}'
ORDER BY created_at DESC;
```

## Step 3: Present Runs Table

| # | Run Name | Created | Items | Description | Metadata |
|---|----------|---------|-------|-------------|----------|

To get item count per run, use the REST API for each run:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-run-items?runName={RUN_NAME}&datasetId={DATASET_ID}&limit=1"
```

Check `meta.totalItems` in the response.

Alternatively, via ClickHouse:

```sql
SELECT dataset_run_name, COUNT(*) AS item_count
FROM dataset_run_items_rmt
WHERE project_id = '{PROJECT_ID}'
  AND dataset_id = '{DATASET_ID}'
GROUP BY dataset_run_name
ORDER BY dataset_run_name;
```

Run via: `docker exec langfuse-clickhouse clickhouse-client --query "..."`.

## Step 4: Inspect a Specific Run

When the user selects a run, fetch its items:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-run-items?runName={RUN_NAME}&datasetId={DATASET_ID}&limit=50"
```

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

Present run items:

| # | Item ID | Trace ID | Created |
|---|---------|----------|---------|

## Step 5: Suggest Next Actions

- To analyze scores for a run → "Use the `analyze-experiment-results` skill."
- To compare this run with another → "Use the `compare-experiments` skill."
- To view a trace in detail → Provide URL: `{HOST}/project/{PROJECT_ID}/traces/{TRACE_ID}`
- To view the run in Langfuse UI → `{HOST}/project/{PROJECT_ID}/datasets/{DATASET_ID}/runs/{RUN_ID}`

Refer to `references/dataset-runs-api-reference.md` for complete API details.
