---
name: create-dataset
description: >-
  This skill should be used when the user wants to create a new Langfuse dataset,
  set up a dataset for benchmarking, or create a dataset with input/output schema validation.
  Trigger phrases include "create dataset", "new dataset", "set up dataset", "add dataset".
---

Create a new Langfuse dataset via the REST API. Optionally configure input and expected output JSON schemas for item validation.

## Step 1: Gather Requirements

Ask the user:
1. **Dataset name** — use folder-style naming with `/` for organization (e.g., `benchmarks/ssp-controls`, `regression/html-tags`).
2. **Description** — brief purpose description.
3. **Input schema** — does the user want to enforce a JSON Schema on item inputs? If yes, help design it (delegate to `design-dataset-schema` skill).
4. **Expected output schema** — does the user want to enforce expected output structure?

## Step 2: Check for Existing Dataset

Before creating, verify no dataset with the same name exists:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets/{name}"
```

If it exists, warn the user that creating with the same name will **upsert** (update metadata/schemas on the existing dataset).

## Step 3: Create Dataset

```bash
curl -s -X POST \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{dataset_name}",
    "description": "{description}",
    "metadata": {},
    "inputSchema": null,
    "expectedOutputSchema": null
  }'
```

Set `inputSchema` and `expectedOutputSchema` to JSON Schema objects if the user wants validation, or `null` to skip.

## Step 4: Verify

Fetch the created dataset back:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets/{name}"
```

Confirm:
- Name matches
- Schemas are applied (if requested)
- Created timestamp is recent

## Step 5: Report

Provide:
1. The dataset ID and name.
2. The Langfuse UI URL: `{HOST}/project/{PROJECT_ID}/datasets/{DATASET_ID}`.
3. Suggest next steps:
   - "Use the `langfuse-dataset-expert` agent to add items."
   - "Use the `design-dataset-schema` skill if you want to add schemas later."

## Naming Conventions

- Use `/` for folder organization: `benchmarks/ssp-controls`, `regression/html-tags`
- Use lowercase with hyphens: `my-benchmark-dataset`
- Include pipeline name for clarity: `ssp-ac-controls`, `html-controls-full-catalog`
- Avoid spaces and special characters beyond `-`, `_`, `/`

## Schema Validation

When `inputSchema` or `expectedOutputSchema` is set:
- Items that fail validation are **rejected** with error details
- Items that pass are created normally
- Schemas follow standard JSON Schema (draft-07)
- Schema validation applies to new items and upserts

Example input schema for an SSP pipeline dataset:
```json
{
  "type": "object",
  "required": ["catalog_id", "control_id", "request"],
  "properties": {
    "catalog_id": { "type": "string", "format": "uuid" },
    "control_id": { "type": "string" },
    "request": {
      "type": "object",
      "required": ["system_characteristics"],
      "properties": {
        "system_characteristics": { "type": "object" }
      }
    }
  }
}
```
