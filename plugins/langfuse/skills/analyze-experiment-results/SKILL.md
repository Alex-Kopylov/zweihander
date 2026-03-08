---
name: analyze-experiment-results
description: >-
  This skill should be used when the user wants to analyze experiment results, inspect scores
  from a dataset run, check pass/fail rates, review per-item outputs, or deep-dive into
  experiment performance. Trigger phrases include "analyze results", "experiment scores",
  "how did the experiment perform", "show results", "inspect run", "experiment analysis".
---

Analyze the results of a Langfuse experiment run: aggregate scores, per-item details, pass/fail rates, and output inspection.

## Step 1: Identify the Run

If the user specifies a run name, use it. Otherwise, list recent runs (via `list-dataset-runs` skill) and let the user choose.

Get the run ID and dataset ID:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/datasets/{DATASET_NAME}/runs"
```

## Step 2: Fetch Run Items

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-run-items?runName={RUN_NAME}&datasetId={DATASET_ID}&limit=100"
```

Collect all `traceId` values — these link to the actual experiment traces.

## Step 3: Fetch Scores per Item

**Important:** Traces, scores, and run items live in **ClickHouse**, not Postgres. Use the REST API or ClickHouse direct queries.

### Via REST API (preferred)

Fetch scores per trace:
```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/scores?traceId={TRACE_ID}"
```

Loop over all trace IDs from Step 2 and collect scores.

### Via ClickHouse (for bulk aggregation)

```sql
SELECT dri.dataset_item_id, dri.trace_id,
       s.name AS score_name, s.value, s.data_type, s.source, s.comment
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
ORDER BY dri.dataset_item_id, s.name;
```

Run via: `docker exec langfuse-clickhouse clickhouse-client --query "..."`.

## Step 4: Aggregate Score Statistics

For each numeric score name, compute via ClickHouse:

```sql
SELECT s.name,
       COUNT(*) AS count,
       round(AVG(s.value), 4) AS mean,
       round(quantile(0.5)(s.value), 4) AS median,
       MIN(s.value) AS min,
       MAX(s.value) AS max,
       round(stddevPop(s.value), 4) AS stddev
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
  AND s.data_type = 'NUMERIC'
GROUP BY s.name
ORDER BY s.name;
```

Note: ClickHouse uses `quantile(0.5)()` instead of Postgres `PERCENTILE_CONT`, and `stddevPop()` instead of `STDDEV`.

Present as:

| Score Name | Count | Mean | Median | Min | Max | StdDev |
|------------|-------|------|--------|-----|-----|--------|

For categorical scores:

```sql
SELECT s.name, s.string_value, COUNT(*) AS count
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
  AND s.data_type = 'CATEGORICAL'
GROUP BY s.name, s.string_value
ORDER BY s.name, count DESC;
```

For boolean scores, show pass/fail rates:

```sql
SELECT s.name,
       countIf(s.value = 1) AS passed,
       countIf(s.value = 0) AS failed,
       COUNT(*) AS total,
       round(100.0 * countIf(s.value = 1) / COUNT(*), 1) AS pass_rate
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
  AND s.data_type = 'BOOLEAN'
GROUP BY s.name
ORDER BY s.name;
```

## Step 5: Per-Item Detail Table

Use the denormalized ClickHouse table (which has inline item data):

```sql
SELECT dri.dataset_item_id AS item_id,
       substring(dri.dataset_item_input, 1, 100) AS input_preview,
       dri.trace_id,
       substring(t.output, 1, 100) AS output_preview,
       groupArray(concat(s.name, '=', toString(round(s.value, 2)))) AS scores
FROM dataset_run_items_rmt dri
LEFT JOIN traces t ON dri.trace_id = t.id AND dri.project_id = t.project_id
LEFT JOIN scores s ON dri.trace_id = s.trace_id
  AND dri.project_id = s.project_id
  AND s.data_type = 'NUMERIC'
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
GROUP BY dri.dataset_item_id, dri.dataset_item_input, dri.trace_id, t.output
ORDER BY dri.dataset_item_id;
```

Note: ClickHouse uses `groupArray()` instead of Postgres `STRING_AGG()`, and `substring()` instead of `SUBSTRING(... FROM ... FOR ...)`.

| Item ID | Input Preview | Trace ID | Output Preview | Scores |
|---------|--------------|----------|----------------|--------|

## Step 6: Identify Failures

Find items with missing or low scores:

- Items with no scores (trace may have failed)
- Items where any score < threshold (e.g., < 0.5 for 0-1 scale)
- Items with error-level observations

```sql
SELECT dri.dataset_item_id, dri.trace_id, t.name AS trace_name
FROM dataset_run_items_rmt dri
LEFT JOIN traces t ON dri.trace_id = t.id AND dri.project_id = t.project_id
LEFT JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_run_id = '{RUN_ID}'
GROUP BY dri.dataset_item_id, dri.trace_id, t.name
HAVING COUNT(s.id) = 0;
```

## Step 7: Report

Present:
1. **Summary** — Run name, dataset, item count, timestamp.
2. **Score overview** — Aggregate statistics table.
3. **Per-item results** — Detailed table with scores.
4. **Failures** — Items that failed or scored below threshold.
5. **Links**:
   - Run URL: `{HOST}/project/{PROJECT_ID}/datasets/{DATASET_ID}/runs/{RUN_ID}`
   - Individual traces: `{HOST}/project/{PROJECT_ID}/traces/{TRACE_ID}`

Suggest next actions:
- "Use `compare-experiments` to compare this run against another."
- "Use `langfuse-eval-manager` to add more evaluators."
- "Use `langfuse-dataset-expert` to update items that consistently fail."

Refer to `references/experiment-data-model-reference.md` for the complete data model.
