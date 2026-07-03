---
name: design-dataset-schema
description: >-
  This skill should be used when the user needs help designing the input or expected output schema
  for Langfuse dataset items. This includes deciding what fields to include, how to structure item
  inputs for specific pipelines, and creating JSON Schema validation rules. Trigger phrases include
  "design schema", "item format", "what should my dataset items look like", "dataset item structure".
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

Help the user design dataset item `input` structures and optional `expectedOutput` structures that fit the target pipeline and produce meaningful experiment results.

## Harness Adaptation

Depending on who you are as an AI agent, load exactly one metadata-linked reference and skip every non-matching file.

## Step 1: Identify the Target Pipeline

Ask the user what application or endpoint the dataset items will be used with. This determines the item schema.

Common patterns:

### REST API Endpoint Pattern

When items will be POSTed to an HTTP endpoint (e.g., via webhook experiment):

```json
{
  "path_param_1": "value",
  "path_param_2": "value",
  "request": {
    "body_field_1": "...",
    "body_field_2": "..."
  }
}
```

**Principle:** Separate path parameters from the request body. The experiment runner uses path parameters to construct the URL and the `request` object as the POST body.

### SDK Experiment Pattern

When items will be used with `dataset.run_experiment(task=my_task)`:

```json
{
  "question": "What is...",
  "context": "Optional context...",
  "config": {
    "model": "gpt-4o",
    "temperature": 0.7
  }
}
```

**Principle:** Include everything the task function needs to produce an output.

## Step 2: Design the Input Schema

### For HTTP Endpoint Pipelines

Examine the target endpoint's request schema. The item `input` should contain:

1. **Path parameters** — extracted for URL construction (top-level keys).
2. **Request body** — the full request payload under a `request` key.
3. **Optional overrides** — model, cache settings, etc.

Example for a generation endpoint `POST /api/v1/ssp/catalogs/{catalog_id}/{control_id}/generate`:

```json
{
  "catalog_id": "bc413ad0-23d7-4ff0-a7af-b48a03294873",
  "control_id": "ac-1",
  "request": {
    "system_characteristics": {
      "system_name": "My System",
      "description": "Description of the system",
      "components": [...],
      "props": {...},
      "responsible_parties": [...]
    },
    "policy": null,
    "procedure": null,
    "reference_content": null
  }
}
```

### For SDK Task Functions

Design based on what the task function expects. The item is passed directly as `item.input`:

```json
{
  "prompt": "Generate a summary of...",
  "context": "Background information...",
  "max_tokens": 500
}
```

## Step 3: Design the Expected Output Schema

`expectedOutput` is optional but valuable for:

- **Automated evaluation**: Evaluators compare actual output against expected.
- **Regression detection**: Verify outputs haven't degraded.
- **Human review**: Annotators set expected outputs as ground truth.

Common patterns:

### Exact Match
```json
{ "answer": "The capital of France is Paris." }
```

### Key Points
```json
{
  "must_contain": ["NIST SP 800-53", "access control"],
  "must_not_contain": ["placeholder", "TODO"],
  "min_length": 200
}
```

### Structured Evaluation Criteria
```json
{
  "criteria": {
    "accuracy": "Must reference the correct control family",
    "completeness": "Must cover all enhancement items",
    "tone": "Professional, technical language"
  }
}
```

### No Expected Output

You can omit `expectedOutput`; experiments still produce traces that Langfuse LLM-as-Judge evaluators can score. If the user asks to configure those evaluators next, use the active harness adaptation reference before invoking `langfuse-eval-manager`.

## Step 4: Create JSON Schema (Optional)

If the user wants to enforce validation on the dataset:

### Input Schema Example

```json
{
  "type": "object",
  "required": ["catalog_id", "control_id", "request"],
  "properties": {
    "catalog_id": {
      "type": "string",
      "format": "uuid",
      "description": "OSCAL catalog UUID"
    },
    "control_id": {
      "type": "string",
      "pattern": "^[a-z]{2}-[0-9]+$",
      "description": "Control identifier (e.g., ac-1, sc-7)"
    },
    "request": {
      "type": "object",
      "required": ["system_characteristics"],
      "properties": {
        "system_characteristics": {
          "type": "object",
          "required": ["system_name", "description"],
          "properties": {
            "system_name": { "type": "string" },
            "description": { "type": "string" }
          }
        }
      }
    }
  },
  "additionalProperties": false
}
```

Apply the schema when creating the dataset:

```bash
curl -s -X POST \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "{dataset_name}",
    "inputSchema": { ... JSON Schema ... }
  }'
```

## Step 5: Validate with a Test Item

Create one test item and verify it passes schema validation:

```bash
curl -s -X POST \
  -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/dataset-items" \
  -H "Content-Type: application/json" \
  -d '{
    "datasetName": "{dataset_name}",
    "input": { ... test item ... }
  }'
```

If configured schema validation fails, use the response error details to fix the schema or item, then retry.

Refer to `references/dataset-schema-patterns.md` for common schema patterns across different pipeline types.
