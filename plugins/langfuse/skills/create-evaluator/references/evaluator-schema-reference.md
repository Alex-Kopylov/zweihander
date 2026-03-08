# Evaluator Schema Reference

Single source of truth for all evaluator-related database schemas, formats, and patterns.

## `eval_templates` Table

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | text | PK | CUID format required (`c` + 24 alphanumeric chars). Non-CUID IDs crash the UI. |
| `project_id` | text | NOT NULL | Langfuse project ID. |
| `name` | text | NOT NULL | Evaluator name identifier (e.g., `no_markdown`, `factuality`). |
| `version` | int | NOT NULL | Auto-incremented per evaluator name. First version = 1. |
| `prompt` | text | NOT NULL | Evaluation prompt text. Uses `{{variable}}` syntax for variable substitution. |
| `model` | text | nullable | Model name (e.g., `gpt-4o`). Must match a model configured in Langfuse `llm_api_keys`. |
| `provider` | text | nullable | Provider name (e.g., `azure`). Must match configured provider. |
| `model_params` | jsonb | nullable | Model parameters. Default: `{"temperature": 0, "max_tokens": 500}` |
| `vars` | text[] | nullable | Array of variable names from the prompt. e.g., `{output}` or `{input,output}`. |
| `output_schema` | jsonb | NOT NULL | See `output_schema` format below. |
| `partner` | text | nullable | Internal Langfuse field. Omit from INSERT. |
| `created_at` | timestamptz | DEFAULT now() | Auto-managed. Omit from INSERT. |
| `updated_at` | timestamptz | DEFAULT now() | Auto-managed. Omit from INSERT. |

**Unique constraint**: `(project_id, name, version)`

## `job_configurations` Table

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | text | PK | CUID format required. |
| `project_id` | text | NOT NULL | Same as template's project_id. |
| `job_type` | enum | NOT NULL | Always `'EVAL'`. Enum values: `EVAL`. |
| `eval_template_id` | text | FK → eval_templates.id | References the eval template. |
| `score_name` | text | NOT NULL | Name of the score that appears in Langfuse UI. |
| `filter` | jsonb | NOT NULL | Trace filter conditions. `'[]'::jsonb` for no filter (match all). |
| `target_object` | text | NOT NULL | `'trace'` for trace-level evaluation. |
| `variable_mapping` | jsonb | NOT NULL | Maps template `{{variables}}` to trace data. See format below. |
| `sampling` | numeric(65,30) | NOT NULL | `1.0` = evaluate 100% of matching traces. Range: 0.0–1.0. |
| `delay` | int | NOT NULL | Milliseconds to wait before executing (e.g., `30000` for 30s, `0` for immediate). |
| `status` | enum | NOT NULL | `'ACTIVE'` or `'INACTIVE'`. Always insert as `'INACTIVE'` for safety. |
| `time_scope` | text[] | NOT NULL | `ARRAY['NEW']` (safe) or `ARRAY['NEW', 'EXISTING']` (triggers backfill). |
| `created_at` | timestamptz | DEFAULT now() | Auto-managed. Omit from INSERT. |
| `updated_at` | timestamptz | DEFAULT now() | Auto-managed. Omit from INSERT. |

---

## `output_schema` Format

The `output_schema` is a flat JSON object with exactly two keys: `reasoning` and `score`. The values are **LLM instruction strings** — descriptions passed to the LLM telling it what to produce for each field. They are NOT type descriptors or JSON Schema.

### Correct examples

```json
{"reasoning": "string", "score": "string"}
```

```json
{"reasoning": "Step-by-step analysis explaining the score", "score": "Score between 0 and 1, where 1 means fully factual"}
```

```json
{"reasoning": "Detailed explanation of why the output does or does not contain markdown", "score": "1 if plain text (pass), 0 if markdown found (fail)"}
```

### Incorrect examples — these will crash the UI

```json
{"reasoning": {"type": "string"}, "score": {"type": "number"}}
```
*Wrong: nested objects instead of flat strings.*

```json
{"analysis": "string", "rating": "string"}
```
*Wrong: keys must be exactly `reasoning` and `score`.*

```json
{"reasoning": "string"}
```
*Wrong: both keys are required.*

---

## `variable_mapping` Format

A JSON array of objects mapping each `{{templateVariable}}` in the prompt to a trace or observation field. Uses camelCase field names.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `templateVariable` | string | yes | Name of the `{{variable}}` in the prompt template (without braces). |
| `langfuseObject` | string | yes | Source object type. See valid values below. |
| `objectName` | string | conditional | Required when `langfuseObject` is not `"trace"`. Name of the specific observation. Omit or `null` for traces. |
| `selectedColumnId` | string | yes | Column to extract from the object. |
| `jsonSelector` | string | no | JSONPath to extract a sub-field (e.g., `"$.output"`), or `null` for the full value. |

### Valid `langfuseObject` values

`trace`, `generation`, `span`, `event`, `embedding`, `agent`, `tool`, `chain`, `retriever`, `evaluator`, `guardrail`, `dataset_item`

### Valid `selectedColumnId` values

`input`, `output`, `metadata`

### Examples

**Trace-level, single variable (output only):**

```json
[
  {
    "templateVariable": "output",
    "langfuseObject": "trace",
    "selectedColumnId": "output",
    "jsonSelector": null
  }
]
```

**Trace-level, input + output:**

```json
[
  {
    "templateVariable": "input",
    "langfuseObject": "trace",
    "selectedColumnId": "input",
    "jsonSelector": null
  },
  {
    "templateVariable": "output",
    "langfuseObject": "trace",
    "selectedColumnId": "output",
    "jsonSelector": null
  }
]
```

**Generation-level (reads from a specific generation span):**

```json
[
  {
    "templateVariable": "output",
    "langfuseObject": "generation",
    "objectName": "html_controls_generation",
    "selectedColumnId": "output",
    "jsonSelector": "$.output"
  }
]
```

---

## `filter` Format

A JSON array of condition objects. Empty `[]` matches all traces.

### Condition schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `column` | string | yes | The filterable column name. |
| `operator` | string | yes | Comparison operator. |
| `type` | string | yes | Filter type: `string`, `stringOptions`, or `arrayOptions`. |
| `value` | string or string[] | yes | The filter value. String for `string` type, array for `*Options` types. |
| `key` | string | no | Optional. Used with some filter types. Typically `null` or omitted. |

### All operators

| Operator | Compatible types |
|----------|-----------------|
| `=` | `string` |
| `<>` | `number` |
| `contains` | `string` |
| `does not contain` | `string` |
| `starts with` | `string` |
| `ends with` | `string` |
| `any of` | `stringOptions`, `arrayOptions` |
| `none of` | `stringOptions`, `arrayOptions` |
| `all of` | `arrayOptions` |

### All filterable columns

| Column | Filter Type(s) | Description |
|--------|----------------|-------------|
| `name` | `string`, `stringOptions` | Trace name |
| `environment` | `stringOptions` | Deployment environment |
| `tags` | `arrayOptions` | Trace tags array |
| `level` | `stringOptions` | Observation level: `DEFAULT`, `DEBUG`, `WARNING`, `ERROR` |
| `userId` | `string` | User ID on the trace |

### Filter examples

**String filter — match trace name containing a substring:**

```json
[
  {
    "column": "name",
    "operator": "contains",
    "type": "string",
    "value": "html_controls",
    "key": null
  }
]
```

**stringOptions filter — match specific trace names:**

```json
[
  {
    "column": "name",
    "operator": "any of",
    "type": "stringOptions",
    "value": ["celery:generate_html_controls", "celery:generate_ssp_controls"]
  }
]
```

**arrayOptions filter — match traces with specific tags:**

```json
[
  {
    "column": "tags",
    "operator": "any of",
    "type": "arrayOptions",
    "value": ["production", "v2"]
  }
]
```

**Environment filter:**

```json
[
  {
    "column": "environment",
    "operator": "any of",
    "type": "stringOptions",
    "value": ["production"]
  }
]
```

**Combined filters (multiple conditions are AND-ed):**

```json
[
  {
    "column": "name",
    "operator": "any of",
    "type": "stringOptions",
    "value": ["celery:generate_html_controls"]
  },
  {
    "column": "environment",
    "operator": "any of",
    "type": "stringOptions",
    "value": ["production"]
  }
]
```

---

## Common Evaluator Patterns

| Evaluation Type | Prompt Structure | Variables | Output Schema |
|----------------|-----------------|-----------|---------------|
| **Factuality** | Provide input context + output, ask LLM to check if output is factually consistent with input | `input`, `output` | `{"reasoning": "Analysis of factual consistency", "score": "1 if factual, 0 if not"}` |
| **Relevance** | Provide input question + output answer, ask if answer is relevant to the question | `input`, `output` | `{"reasoning": "Analysis of relevance to the question", "score": "Score 0-1, where 1 is fully relevant"}` |
| **Tone** | Provide output text, ask if it matches the desired tone (professional, friendly, etc.) | `output` | `{"reasoning": "Analysis of tone characteristics", "score": "1 if tone matches, 0 if not"}` |
| **No Markdown** | Provide output text, check for any markdown formatting | `output` | `{"reasoning": "Description of any markdown found", "score": "1 if plain text, 0 if markdown found"}` |
| **Completeness** | Provide input request + output response, check if all aspects are addressed | `input`, `output` | `{"reasoning": "Analysis of which aspects are addressed", "score": "Score 0-1 based on completeness"}` |
| **Hallucination** | Provide input context + output, check for claims not supported by input | `input`, `output` | `{"reasoning": "Analysis of unsupported claims", "score": "1 if no hallucination, 0 if hallucination found"}` |

---

## `model_params` Defaults

```json
{"temperature": 0, "max_tokens": 500}
```

- `temperature: 0` ensures deterministic evaluation results.
- `max_tokens: 500` is sufficient for reasoning + score output.
- Adjust as needed for evaluators requiring longer reasoning chains.

---

## Note on CUID Versions

**Note on CUID versions:** Langfuse's Prisma schema uses `@default(cuid())` (CUID v1) for auto-generated IDs. This plugin uses `cuid2` for manually generated IDs. Both formats are compatible -- Langfuse accepts either.
