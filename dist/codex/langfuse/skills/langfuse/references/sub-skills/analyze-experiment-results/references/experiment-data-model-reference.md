# Experiment Data Model Reference

Complete data model for Langfuse experiments: how datasets, runs, items, traces, and scores connect.

## Entity Relationships

```
Dataset
  ├── DatasetItem (1:N) — test cases in the dataset
  │     ├── input: jsonb — item input data
  │     ├── expectedOutput: jsonb — expected result
  │     └── metadata: jsonb — item metadata
  │
  └── DatasetRun (1:N) — experiment executions
        └── DatasetRunItem (1:N) — per-item results
              ├── datasetItemId → DatasetItem — which item was tested
              └── traceId → Trace — the trace produced
                    └── Score (1:N) — evaluation scores on the trace
                          ├── name: text — score name (e.g., "accuracy")
                          ├── value: float — numeric value
                          ├── dataType: NUMERIC | CATEGORICAL | BOOLEAN
                          └── source: API | ANNOTATION | EVAL
```

## How Experiments Flow

### 1. Dataset Preparation
- Create a `Dataset` with optional schemas.
- Add `DatasetItem`s — each contains an `input` and optional `expectedOutput`.

### 2. Experiment Execution
- An experiment run creates a `DatasetRun` linked to the dataset.
- For each `DatasetItem`, a `DatasetRunItem` links the tested `datasetItemId` to the produced `traceId`.

### 3. Scoring
Scores are attached to **traces**, not directly to run items. The link is:
`DatasetRunItem.traceId → Trace → Score`

Scores come from three sources:
- **EVAL**: LLM-as-a-Judge evaluators configured in Langfuse (automatic)
- **API**: Programmatic scores via SDK/API (custom evaluators)
- **ANNOTATION**: Human annotations via Langfuse UI

### 4. Analysis
To analyze an experiment, join: `dataset_run_items → traces → scores`.
To compare experiments, join the same chain across multiple runs.

## Database Tables

### `datasets`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | PK (with project_id) |
| `name` | text | Unique per project |
| `project_id` | text | FK to projects |
| `description` | text | |
| `metadata` | jsonb | |
| `input_schema` | json | JSON Schema for item inputs |
| `expected_output_schema` | json | JSON Schema for expected outputs |
| `remote_experiment_url` | text | Webhook URL (DB-only field) |
| `remote_experiment_payload` | jsonb | Default webhook payload (DB-only field) |

### `dataset_items`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | PK (with project_id, valid_from) |
| `dataset_id` | text | FK to datasets |
| `project_id` | text | |
| `input` | jsonb | Item input |
| `expected_output` | jsonb | Expected output |
| `metadata` | jsonb | |
| `status` | DatasetStatus | `ACTIVE` / `ARCHIVED` |
| `source_trace_id` | text | Link to source trace |
| `source_observation_id` | text | Link to source observation |
| `is_deleted` | boolean | Soft delete |
| `valid_from` | timestamp | Version start |
| `valid_to` | timestamp | Version end (NULL = current) |

### `dataset_runs`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | PK (with project_id) |
| `name` | text | Unique per (dataset_id, project_id) |
| `dataset_id` | text | FK to datasets |
| `project_id` | text | |
| `description` | text | |
| `metadata` | jsonb | Experiment config |

### `dataset_run_items`

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | PK (with project_id) |
| `dataset_run_id` | text | FK to dataset_runs |
| `dataset_item_id` | text | FK to dataset_items |
| `trace_id` | text | The produced trace |
| `observation_id` | text | Optional (backwards compat) |
| `project_id` | text | |

### `traces` (referenced, not experiment-specific)

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | Trace ID |
| `name` | text | Trace name |
| `input` | jsonb | Trace input |
| `output` | jsonb | Trace output |
| `metadata` | jsonb | |
| `tags` | text[] | |

### `scores` (referenced, not experiment-specific)

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | Score ID |
| `trace_id` | text | FK to traces |
| `observation_id` | text | Optional |
| `name` | text | Score name |
| `value` | float | Numeric value |
| `string_value` | text | Categorical value |
| `data_type` | ScoreDataType | `NUMERIC`, `CATEGORICAL`, `BOOLEAN` |
| `source` | ScoreSource | `API`, `ANNOTATION`, `EVAL` |
| `comment` | text | Optional comment |

## Storage Architecture Note

Langfuse uses a **hybrid storage model**:
- **PostgreSQL**: `datasets`, `dataset_items`, `dataset_runs` (metadata and config)
- **ClickHouse**: `traces`, `scores`, `dataset_run_items_rmt` (runtime/analytics data)

The Postgres `traces`, `scores`, and `dataset_run_items` tables exist but are empty; query ClickHouse for runtime data.

**For analysis queries**, use the REST API (preferred; it reads ClickHouse transparently), direct ClickHouse (`docker exec langfuse-clickhouse clickhouse-client --query "..."`), or the two-step REST pattern below.

## Key Queries

### Via REST API (preferred)

**Get run items:**
```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-run-items?runName={RUN_NAME}&datasetId={DATASET_ID}&limit=100"
```

**Get scores for a trace:**
```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/scores?traceId={TRACE_ID}"
```

**Two-step analysis pattern:**
1. Fetch all run items (get traceIds)
2. For each traceId, fetch scores
3. Aggregate in the client

### Via ClickHouse (for complex aggregations)

**Full experiment result (items + scores):**
```sql
SELECT
    dri.dataset_item_id AS item_id,
    dri.dataset_item_input AS item_input,
    dri.dataset_item_expected_output AS expected_output,
    dri.trace_id,
    t.output AS trace_output,
    s.name AS score_name,
    s.value AS score_value,
    s.data_type,
    s.source AS score_source
FROM dataset_run_items_rmt dri
LEFT JOIN traces t ON dri.trace_id = t.id AND dri.project_id = t.project_id
LEFT JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
    AND dri.dataset_run_id = '{RUN_ID}'
ORDER BY dri.dataset_item_id, s.name;
```

**Score summary per run:**
```sql
SELECT
    s.name,
    s.data_type,
    COUNT(*) AS count,
    AVG(s.value) AS mean,
    MIN(s.value) AS min,
    MAX(s.value) AS max,
    stddevPop(s.value) AS stddev
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
    AND dri.dataset_run_id = '{RUN_ID}'
    AND s.data_type = 'NUMERIC'
GROUP BY s.name, s.data_type
ORDER BY s.name;
```

Note: ClickHouse uses `stddevPop()` instead of Postgres `STDDEV()`.

**Items with no scores (potential failures):**
```sql
SELECT dri.dataset_item_id, dri.trace_id
FROM dataset_run_items_rmt dri
LEFT JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
    AND dri.dataset_run_id = '{RUN_ID}'
GROUP BY dri.dataset_item_id, dri.trace_id
HAVING COUNT(s.id) = 0;
```

## Langfuse Documentation References

- [Experiments Data Model](https://langfuse.com/docs/evaluation/experiments/data-model)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Remote Dataset Runs](https://langfuse.com/docs/evaluation/dataset-runs/remote-run)
- [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets)
