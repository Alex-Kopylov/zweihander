---
name: trigger-experiment
description: >-
  This skill should be used when the user wants to trigger an experiment, run an experiment,
  start a dataset run, execute a benchmark, or send a webhook to start an experiment.
  Trigger phrases include "trigger experiment", "run experiment", "start experiment",
  "execute benchmark", "run dataset", "POST webhook".
---

Trigger a Langfuse experiment against a dataset. Supports two methods: webhook-based (remote experiment trigger) and SDK-based (programmatic).

## Method 1: Webhook Trigger (Remote Experiment)

Use when the dataset has `remote_experiment_url` configured. This is the Langfuse "Custom Experiment" pattern.

### Step 1: Verify Dataset and Remote Config

Check the dataset exists and has a webhook URL configured:

```sql
SELECT id, name, remote_experiment_url, remote_experiment_payload
FROM datasets
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

If `remote_experiment_url` is NULL, use the `configure-remote-experiment` skill first.

### Step 2: Build Webhook Payload

The payload mimics what Langfuse sends when a user clicks "Run" in the Custom Experiment UI:

```json
{
  "projectId": "{PROJECT_ID}",
  "datasetName": "{DATASET_NAME}",
  "datasetId": "{DATASET_ID}",
  "payload": "{\"model\": \"gpt-4o\", \"name\": \"experiment-name\", \"item_timeout\": 300, \"experiment_timeout\": 1800}"
}
```

**Critical:** The `payload` field is a **JSON-encoded string**, not a nested object. This matches Langfuse's webhook format.

### Step 3: Send Webhook

```bash
curl -s -X POST \
  "{REMOTE_EXPERIMENT_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "{PROJECT_ID}",
    "datasetName": "{DATASET_NAME}",
    "datasetId": "{DATASET_ID}",
    "payload": "{...escaped JSON string...}"
  }'
```

The endpoint must respond within **10 seconds** (Langfuse's webhook timeout). A successful response indicates the experiment was accepted (typically queued for async execution).

### Step 4: Monitor

After triggering, check if a dataset run was created:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/datasets/{DATASET_NAME}/runs"
```

Look for a run with a recent `createdAt` timestamp matching the experiment name.

### Payload Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `model` | string | route default | LLM model override |
| `name` | string | auto-generated | Experiment run name. Auto-generated as `{pipeline}-{model}-{ISO timestamp}` if absent |
| `item_timeout` | int | 300 | Per-item timeout in seconds |
| `experiment_timeout` | int | 1800 | Overall experiment timeout in seconds |
| `cache_enabled` | bool | false | Whether to cache LLM results (experiments should default to false) |

Any other key in `payload` matching a route query parameter is passed through.

## Method 2: SDK-Based Experiment

Guide the user through the Python SDK pattern.

### High-Level Runner

```python
from langfuse import Langfuse

langfuse = Langfuse()
dataset = langfuse.get_dataset("{DATASET_NAME}")

def my_task(*, item, **kwargs):
    # item.input contains the dataset item's input
    output = call_your_application(item.input)
    return output

result = dataset.run_experiment(
    name="my-experiment-{timestamp}",
    task=my_task,
    max_concurrency=5,
)

print(result.format())
```

### With Evaluators

```python
from langfuse import Evaluation

def accuracy_eval(*, input, output, expected_output, **kwargs):
    # Custom evaluation logic
    score = compute_score(output, expected_output)
    return Evaluation(name="accuracy", value=score, comment="...")

result = dataset.run_experiment(
    name="my-experiment-{timestamp}",
    task=my_task,
    evaluators=[accuracy_eval],
)
```

### Low-Level (Manual Control)

```python
langfuse = Langfuse()
dataset = langfuse.get_dataset("{DATASET_NAME}")

run_name = f"my-experiment-{datetime.now().isoformat()}"

for item in dataset.items:
    with item.run(run_name=run_name) as root_span:
        output = call_your_application(item.input)
        root_span.score_trace(name="quality", value=0.85)

langfuse.flush()
```

## Choosing a Method

| Criteria | Webhook | SDK |
|----------|---------|-----|
| Trigger from Langfuse UI | Yes | No |
| Non-technical users | Yes | No |
| Custom evaluators | Server-side only | Yes (item + run level) |
| Full control over execution | No | Yes |
| Requires running service | Yes (webhook endpoint) | No (runs locally) |
| Distributed trace linking | Via OTel propagation | Automatic via SDK |

Refer to `references/experiment-webhook-reference.md` for the complete webhook format and trace propagation details.
