---
name: discover-datasets
description: >-
  This skill should be used when the user asks to discover datasets, list datasets, find what datasets exist,
  browse dataset items, inspect dataset contents, check dataset schemas, or explore dataset metadata in their
  Langfuse project. It enumerates all datasets with their items, runs, and schema configurations.
---

Enumerate all datasets in the Langfuse project and present findings in organized tables.

## Step 1: List All Datasets

Query the REST API to get all datasets:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets"
```

Response includes: `name`, `id`, `description`, `metadata`, `inputSchema`, `expectedOutputSchema`, `items[]` (IDs), `runs[]` (names).

If API is unavailable, fall back to DB:

```sql
SELECT id, name, description, metadata,
       input_schema, expected_output_schema,
       remote_experiment_url, remote_experiment_payload,
       created_at, updated_at
FROM datasets
WHERE project_id = '{PROJECT_ID}'
ORDER BY created_at DESC;
```

Note: `remote_experiment_url` and `remote_experiment_payload` are only visible via DB, not the REST API.

## Step 2: Present Dataset Summary

Display a table:

| Name | Items | Runs | Description | Schema | Remote Experiment |
|------|-------|------|-------------|--------|-------------------|

- **Items**: Count from the `items[]` array.
- **Runs**: Count from the `runs[]` array.
- **Schema**: "Yes (input)" / "Yes (output)" / "Yes (both)" / "No" based on `inputSchema`/`expectedOutputSchema`.
- **Remote Experiment**: "Configured" if `remote_experiment_url` is set (DB-only check), otherwise "Not configured" or "Unknown (API-only)".

## Step 3: Inspect a Specific Dataset

When the user selects a dataset, fetch its full details:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets/{name}"
```

This returns the dataset with full item objects (including `input`, `expectedOutput`, `metadata`) and run names.

Present items in a table:

| # | Item ID | Status | Source Trace | Input Summary | Expected Output |
|---|---------|--------|--------------|---------------|-----------------|

Truncate long `input`/`expectedOutput` values to first 100 chars with `...`.

## Step 4: Inspect Dataset Items

To get paginated items (useful for large datasets):

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/dataset-items?datasetName={name}&limit=50&page=1"
```

## Step 5: Check Item Version History (DB Only)

To see all versions of a specific item:

```sql
SELECT id, input, expected_output, status, is_deleted,
       valid_from, valid_to, created_at, updated_at
FROM dataset_items
WHERE project_id = '{PROJECT_ID}'
  AND id = '{ITEM_ID}'
ORDER BY valid_from DESC;
```

Current version has `valid_to IS NULL`.

## Step 6: Suggest Next Actions

Based on discovered data, suggest:

- If dataset has no items → "Use the `langfuse-dataset-expert` agent to populate it."
- If dataset has items but no runs → "Use the `langfuse-experiment-manager` agent to run experiments."
- If dataset has no schema → "Consider adding input/output schemas for validation."
- If remote experiment URL is not configured → "Use the `langfuse-experiment-manager` agent to configure remote triggering."

Refer to `references/datasets-api-reference.md` for complete API details.
