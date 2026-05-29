---
name: configure-remote-experiment
description: >-
  This skill should be used when the user wants to configure a Langfuse dataset for remote experiment
  triggering from the UI, set up a webhook URL, update the default experiment payload, or enable the
  Custom Experiment feature. Trigger phrases include "configure remote experiment", "set webhook URL",
  "enable custom experiment", "set up experiment trigger", "configure dataset webhook".
---

Configure `remote_experiment_url` and `remote_experiment_payload` on a Langfuse dataset to enable Custom Experiment triggers from the Langfuse UI.

## Step 1: Identify the Dataset

Ask the user which dataset to configure. Use `discover-datasets` if needed to list available datasets.

Verify the dataset exists:

```bash
curl -s -u "$PUBLIC_KEY:$SECRET_KEY" "$HOST/api/public/datasets/{DATASET_NAME}"
```

## Step 2: Gather Configuration

Ask the user for:

1. **Webhook URL** — The endpoint that receives experiment trigger requests.
   - Example: `https://your-service/api/v1/experiments/trigger`
   - For local development: `http://localhost:8000/api/v1/experiments/trigger`
   - Note: Langfuse does NOT send auth headers — endpoint must be network-isolated or use URL-based tokens.

2. **Default payload** (optional) — JSON object sent with every trigger and overridable per-trigger in the UI.
   Common payload fields:
   ```json
   {
     "model": "gpt-4o",
     "item_timeout": 300,
     "experiment_timeout": 1800,
     "cache_enabled": false
   }
   ```

## Step 3: Check Current Configuration

Read current DB values (not available via REST API):

```sql
SELECT name, remote_experiment_url, remote_experiment_payload
FROM datasets
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

If already configured, show current values and ask if user wants to update.

## Step 4: Apply Configuration

**These fields are only writable via direct DB access.**

### Via psycopg2 (preferred)

```python
import psycopg2
import json

conn = psycopg2.connect("{DB_CONN}")
cur = conn.cursor()
cur.execute("""
    UPDATE datasets
    SET remote_experiment_url = %s,
        remote_experiment_payload = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE project_id = %s AND name = %s
""", (
    "{WEBHOOK_URL}",
    json.dumps({PAYLOAD_DICT}),
    "{PROJECT_ID}",
    "{DATASET_NAME}",
))
conn.commit()
cur.close()
conn.close()
```

### Via docker exec psql (fallback)

```bash
docker exec {CONTAINER} psql -U {DB_USER} -d {DB_NAME} -c "
  UPDATE datasets
  SET remote_experiment_url = '{WEBHOOK_URL}',
      remote_experiment_payload = '{ESCAPED_JSON}'::jsonb,
      updated_at = CURRENT_TIMESTAMP
  WHERE project_id = '{PROJECT_ID}'
    AND name = '{DATASET_NAME}';
"
```

**Escape single quotes in JSON** when using docker exec: replace `'` with `''`.

## Step 5: Verify

Re-read from DB to confirm:

```sql
SELECT name, remote_experiment_url, remote_experiment_payload, updated_at
FROM datasets
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

## Step 6: Test the Webhook (Optional)

Send a test trigger to verify the endpoint responds:

```bash
curl -s -X POST "{WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "{PROJECT_ID}",
    "datasetName": "{DATASET_NAME}",
    "datasetId": "{DATASET_ID}",
    "payload": "{\"model\": \"gpt-4o\", \"item_timeout\": 300}"
  }'
```

Expected: 200 response within 10 seconds (Langfuse's webhook timeout).

## Step 7: Report

Provide:
1. Confirmation of the configured URL and payload.
2. Instructions for triggering from the Langfuse UI:
   - Navigate to Project → Datasets → Select dataset
   - Click "Start Experiment" → `⚡` Custom Experiment
   - The URL and default payload are pre-configured
   - Optionally modify the payload before clicking "Run"
3. The dataset UI URL: `{HOST}/project/{PROJECT_ID}/datasets/{DATASET_ID}`

## Removing Remote Experiment Configuration

To disable the Custom Experiment trigger:

```sql
UPDATE datasets
SET remote_experiment_url = NULL,
    remote_experiment_payload = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

Refer to `references/remote-experiment-reference.md` for the webhook payload format and authentication details.
