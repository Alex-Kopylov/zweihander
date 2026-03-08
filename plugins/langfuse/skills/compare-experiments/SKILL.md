---
name: compare-experiments
description: >-
  This skill should be used when the user wants to compare two or more experiment runs,
  detect regressions, see score deltas between runs, or evaluate model performance differences.
  Trigger phrases include "compare runs", "compare experiments", "diff runs", "regression check",
  "which run is better", "model comparison", "A/B comparison".
---

Compare two or more dataset runs side by side: score deltas, per-item regressions, and aggregate performance differences.

**Storage note:** Run items, traces, and scores live in **ClickHouse**, not Postgres. Use the REST API or ClickHouse direct queries for analysis. Run metadata lives in **Postgres**.

## Step 1: Identify Runs to Compare

If the user specifies run names, use them. Otherwise, list recent runs (via `list-dataset-runs` skill) and let the user select two or more.

Collect run IDs from Postgres:

```sql
SELECT id, name, metadata, created_at
FROM dataset_runs
WHERE project_id = '{PROJECT_ID}'
  AND dataset_id = '{DATASET_ID}'
  AND name IN ('{RUN_A_NAME}', '{RUN_B_NAME}')
ORDER BY created_at;
```

## Step 2: Aggregate Score Comparison

Compare aggregate score statistics across runs via ClickHouse:

```sql
SELECT
    dri.dataset_run_name AS run_name,
    s.name AS score_name,
    COUNT(*) AS count,
    round(AVG(s.value), 4) AS mean,
    round(quantile(0.5)(s.value), 4) AS median,
    MIN(s.value) AS min,
    MAX(s.value) AS max
FROM dataset_run_items_rmt dri
JOIN scores s ON dri.trace_id = s.trace_id AND dri.project_id = s.project_id
WHERE dri.project_id = '{PROJECT_ID}'
  AND dri.dataset_id = '{DATASET_ID}'
  AND dri.dataset_run_name IN ('{RUN_A_NAME}', '{RUN_B_NAME}')
  AND s.data_type = 'NUMERIC'
GROUP BY dri.dataset_run_name, s.name
ORDER BY s.name, dri.dataset_run_name;
```

Run via: `docker exec langfuse-clickhouse clickhouse-client --query "..."`.

Present as a comparison table:

| Score | Run A Mean | Run B Mean | Delta | Better |
|-------|-----------|-----------|-------|--------|

Delta = Run B - Run A. "Better" column: ↑ (improved), ↓ (regressed), = (no change).

## Step 3: Per-Item Score Comparison

For the same dataset items, compare scores across runs via ClickHouse:

```sql
SELECT
    dri_a.dataset_item_id AS item_id,
    s_a.name AS score_name,
    s_a.value AS run_a_score,
    s_b.value AS run_b_score,
    round(s_b.value - s_a.value, 4) AS delta
FROM dataset_run_items_rmt dri_a
JOIN scores s_a ON dri_a.trace_id = s_a.trace_id AND dri_a.project_id = s_a.project_id
JOIN dataset_run_items_rmt dri_b ON dri_a.dataset_item_id = dri_b.dataset_item_id
    AND dri_b.project_id = dri_a.project_id
    AND dri_b.dataset_run_id = '{RUN_B_ID}'
JOIN scores s_b ON dri_b.trace_id = s_b.trace_id AND dri_b.project_id = s_b.project_id
    AND s_b.name = s_a.name
WHERE dri_a.project_id = '{PROJECT_ID}'
  AND dri_a.dataset_run_id = '{RUN_A_ID}'
  AND s_a.data_type = 'NUMERIC'
ORDER BY delta ASC;
```

Present items with largest regressions first:

| Item ID | Score | Run A | Run B | Delta |
|---------|-------|-------|-------|-------|

## Step 4: Regression Detection

Identify items where scores decreased:

- Filter per-item comparison for `delta < 0` (or below a threshold).
- Group by item to find items that regressed on multiple scores.
- Highlight items that went from passing to failing (boolean scores: 1 → 0).

```sql
SELECT dri_a.dataset_item_id,
       countIf(s_b.value < s_a.value) AS regressions,
       countIf(s_b.value > s_a.value) AS improvements,
       countIf(s_b.value = s_a.value) AS unchanged
FROM dataset_run_items_rmt dri_a
JOIN scores s_a ON dri_a.trace_id = s_a.trace_id AND dri_a.project_id = s_a.project_id
JOIN dataset_run_items_rmt dri_b ON dri_a.dataset_item_id = dri_b.dataset_item_id
    AND dri_b.project_id = dri_a.project_id
    AND dri_b.dataset_run_id = '{RUN_B_ID}'
JOIN scores s_b ON dri_b.trace_id = s_b.trace_id AND dri_b.project_id = s_b.project_id
    AND s_b.name = s_a.name
WHERE dri_a.project_id = '{PROJECT_ID}'
  AND dri_a.dataset_run_id = '{RUN_A_ID}'
  AND s_a.data_type = 'NUMERIC'
GROUP BY dri_a.dataset_item_id
HAVING countIf(s_b.value < s_a.value) > 0
ORDER BY regressions DESC;
```

Note: ClickHouse uses `countIf()` instead of Postgres `COUNT(*) FILTER (WHERE ...)`.

## Step 5: Metadata Comparison

Compare run metadata from Postgres to understand what changed:

```sql
SELECT name, metadata, created_at
FROM dataset_runs
WHERE project_id = '{PROJECT_ID}'
  AND id IN ('{RUN_A_ID}', '{RUN_B_ID}')
ORDER BY created_at;
```

Common differences: model change, prompt version, temperature, provider.

## Step 6: Report

Present:

1. **Run metadata** — Side-by-side: model, provider, timestamp, item count.
2. **Aggregate comparison** — Score means, medians with deltas.
3. **Regression summary** — Count of items improved / regressed / unchanged per score.
4. **Top regressions** — Items with the largest negative deltas.
5. **Top improvements** — Items with the largest positive deltas.
6. **Verdict** — Overall assessment: "Run B improved on X, regressed on Y."

Links:
- Run A: `{HOST}/project/{PROJECT_ID}/datasets/{DATASET_ID}/runs/{RUN_A_ID}`
- Run B: `{HOST}/project/{PROJECT_ID}/datasets/{DATASET_ID}/runs/{RUN_B_ID}`
