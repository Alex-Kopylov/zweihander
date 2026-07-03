---
name: create-dataset
description: >-
  This skill should be used when the user wants to create a new Langfuse dataset,
  set up a dataset for benchmarking, or create a dataset with input/output schema validation.
  Trigger phrases include "create dataset", "new dataset", "set up dataset", "add dataset".
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

Create a Langfuse dataset via REST API, optionally with input and expected output JSON schemas for item validation.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Step 1: Gather Requirements

Ask the user:
1. **Dataset name** — follow the naming conventions below.
2. **Description** — brief purpose description.
3. **Input schema** — whether to enforce JSON Schema on item inputs; if yes, help design it (delegate to `design-dataset-schema` skill).
4. **Expected output schema** — whether to enforce expected output structure.

## Step 2: Check for Existing Dataset

Before creating, verify no dataset with the same name exists:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets/{name}"
```

If it exists, warn that creating with the same name will **upsert** the existing dataset's metadata/schemas.

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
- Failing items are **rejected** with error details
- Passing items are created normally
- Schemas follow JSON Schema draft-07
- Validation applies to new items and upserts

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
