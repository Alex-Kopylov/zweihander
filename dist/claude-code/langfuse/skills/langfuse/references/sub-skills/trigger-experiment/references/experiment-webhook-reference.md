# Experiment Webhook Reference

Complete reference for the Langfuse Remote Experiment Trigger (Custom Experiment) webhook mechanism.

## Overview

Custom Experiment triggers experiments from the Langfuse UI. Clicking "Run" in the dataset UI sends a POST request to the configured webhook URL. The receiving service fetches the dataset, processes each item, and records results back to Langfuse.

## Webhook Configuration

### Database Fields (on `datasets` table)

| Field | Type | Notes |
|-------|------|-------|
| `remote_experiment_url` | text | Webhook URL. POST target when "Run" is clicked. |
| `remote_experiment_payload` | jsonb | Default payload. Users can modify per-trigger in the UI. |

These fields are **NOT available via REST API**; they require direct DB access.

### Setting via DB

```sql
UPDATE datasets
SET remote_experiment_url = 'https://your-service/api/v1/experiments/trigger',
    remote_experiment_payload = '{"model": "gpt-4o", "item_timeout": 300}'::jsonb
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

### Langfuse UI Configuration

1. Navigate to Project → Datasets → Select dataset
2. Click "Start Experiment" → `⚡` icon under "Custom Experiment"
3. Enter webhook URL and default payload JSON

## Webhook Payload Format

When triggered, Langfuse sends:

```
POST {remote_experiment_url}
Content-Type: application/json
```

```json
{
  "projectId": "local-dev-project",
  "datasetId": "cmkqphpqm001mml076oztd8mk",
  "datasetName": "test",
  "payload": "{\"model\": \"gpt-4o\", \"item_timeout\": 300}"
}
```

**Critical format notes:**
- `projectId`, `datasetId`, `datasetName` are camelCase (Langfuse convention).
- `payload` is a **JSON-encoded string**, not a nested object. The webhook receiver must parse it.
- If the user modifies the payload in the UI before triggering, the modified version is sent.

## Timeout

Langfuse waits **up to 10 seconds** for a response. The webhook receiver must:
1. Accept the request quickly (queue async processing).
2. Return a success response (e.g., `200 {"status": "accepted"}`).
3. Process dataset items asynchronously.

## Authentication

Langfuse does **NOT** currently support sending Authorization headers or custom headers with webhook requests. Authentication must be handled via:
- Network isolation (webhook endpoint only reachable from Langfuse's network)
- URL-based tokens (e.g., `?token=secret` in the URL — not recommended for production)
- IP allowlisting

Reference: [GitHub Discussion #9884](https://github.com/orgs/langfuse/discussions/9884)

## Experiment Execution Pattern

The webhook receiver (your service) follows this pattern:

```
1. Receive webhook POST
2. Validate dataset exists: langfuse.get_dataset(datasetName)
3. Queue async processing (e.g., Celery task)
4. Return 200 within 10 seconds

--- Async processing ---
5. For each dataset item:
   a. item.run(run_name=experiment_name) — creates trace linked to dataset run
   b. Process item (call your LLM application)
   c. Record output on the trace
6. langfuse.flush()
```

## Trace Linking

To nest experiment traces under the dataset run in the Langfuse UI, use one of:

### Option A: SDK `item.run()` Context Manager (Recommended for SDK-based)

```python
with item.run(run_name=experiment_name) as root_span:
    output = my_application(item.input)
    root_span.update_trace(output=output)
```

The SDK automatically creates the `dataset_run` and `dataset_run_item` records linking the trace.

### Option B: OTel Trace Context Propagation (For HTTP-based)

When the experiment runner POSTs to an HTTP endpoint:

```python
from opentelemetry import propagate

headers = {}
propagate.inject(carrier=headers)
response = httpx.post(url, json=body, headers=headers)
```

The receiving endpoint (with OTel middleware) extracts the trace context and creates child spans under the experiment trace. This requires:
1. OTel SDK configured on both sender and receiver.
2. The receiver's OTel middleware extracts `traceparent`/`tracestate` headers.
3. Langfuse's `@observe` decorator detects the OTel context and links spans.

### Option C: Langfuse `propagate_attributes()` (Intra-process only)

```python
from langfuse import propagate_attributes

with item.run(run_name=experiment_name):
    headers = propagate_attributes()
    # Pass headers to downstream calls
```

Note: `propagate_attributes()` propagates **metadata** context within a process. For cross-service HTTP propagation, use OTel context propagation (Option B).

## Python SDK Experiment Runner

For programmatic experiments without a webhook:

```python
from langfuse import Langfuse, Evaluation

langfuse = Langfuse()
dataset = langfuse.get_dataset("my-dataset")

def my_task(*, item, **kwargs):
    return call_application(item.input)

def my_evaluator(*, input, output, expected_output, **kwargs):
    return Evaluation(name="quality", value=0.9, comment="Good output")

result = dataset.run_experiment(
    name="experiment-2026-03-01",
    task=my_task,
    evaluators=[my_evaluator],
    max_concurrency=5,
)

print(result.format())
```

### Evaluator Types

**Item-level:** Receives `input`, `output`, `expected_output`, `metadata`. Returns `Evaluation`.

**Run-level:** Receives `item_results` (all items). Returns aggregate `Evaluation`.

```python
def avg_score(*, item_results, **kwargs):
    scores = [e.value for r in item_results for e in r.evaluations if e.name == "quality"]
    return Evaluation(name="avg_quality", value=sum(scores) / len(scores) if scores else 0)
```

## Langfuse Documentation References

- [Experiments Data Model](https://langfuse.com/docs/evaluation/experiments/data-model)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Remote Dataset Runs](https://langfuse.com/docs/evaluation/dataset-runs/remote-run)
- [Python SDK Reference: experiment module](https://python.reference.langfuse.com/langfuse/experiment)
- [Datasets](https://langfuse.com/docs/evaluation/experiments/datasets)
- [Remote Experiment Trigger Changelog](https://langfuse.com/changelog/2025-07-24-remote-experiment-triggers)
