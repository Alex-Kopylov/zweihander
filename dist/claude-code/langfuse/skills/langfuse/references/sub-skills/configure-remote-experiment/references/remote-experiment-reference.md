# Remote Experiment Configuration Reference

Complete reference for Langfuse Custom Experiment (remote dataset run) configuration and webhook format.

## Overview

The Custom Experiment feature allows non-technical users to trigger experiments from the Langfuse UI. When configured on a dataset, a "Custom Experiment" option appears that POSTs to an external webhook URL.

## Database Fields

On the `datasets` table:

| Column | Type | Notes |
|--------|------|-------|
| `remote_experiment_url` | text | Webhook URL. NULL = feature disabled. |
| `remote_experiment_payload` | jsonb | Default payload. NULL = no default. |

**These fields are not available via REST API.** Read via direct DB query; write via direct DB UPDATE or Langfuse UI configuration.

## Webhook Payload Format

When a user clicks "Run" in the Custom Experiment UI, Langfuse POSTs:

```
POST {remote_experiment_url}
Content-Type: application/json
```

```json
{
  "projectId": "local-dev-project",
  "datasetId": "cmkqphpqm001mml076oztd8mk",
  "datasetName": "test",
  "payload": "{\"model\": \"gpt-4o\", \"item_timeout\": 300, \"experiment_timeout\": 1800}"
}
```

### Field Details

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `projectId` | string | Auto (Langfuse) | Project ID from Langfuse context |
| `datasetId` | string | Auto (Langfuse) | Dataset's CUID |
| `datasetName` | string | Auto (Langfuse) | Dataset name |
| `payload` | string | User-configurable | JSON-encoded string. Default from `remote_experiment_payload`, modifiable per-trigger. |

### Payload String Contents

`payload` is a JSON string that typically parses to:

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `model` | string | varies | LLM model to use |
| `name` | string | auto-generated | Experiment run name |
| `item_timeout` | int | 300 | Per-item processing timeout (seconds) |
| `experiment_timeout` | int | 1800 | Overall experiment timeout (seconds) |
| `cache_enabled` | bool | false | Whether to use LLM cache |
| `pipeline` | string | varies | Pipeline identifier (if webhook handles multiple) |

Additional keys pass through to the application.

## Constraints

### Timeout
Langfuse waits **up to 10 seconds** for a webhook response. The receiver must:
1. Validate the request quickly.
2. Queue async processing (Celery, background task, etc.).
3. Return HTTP 200 with acceptance status.

### Authentication
Langfuse does **NOT** send Authorization headers or custom headers with webhook requests. Security must be handled via:
- Network isolation (internal network only)
- URL-based tokens (not recommended for production)
- IP allowlisting
- VPN/private networking

Reference: [GitHub Discussion #9884](https://github.com/orgs/langfuse/discussions/9884)

### Endpoint Requirements
The webhook endpoint should:
- Accept POST with JSON body
- Parse `payload` from JSON string to dict
- Validate the dataset exists in Langfuse
- Queue async processing
- Return within 10 seconds

### Example Response
```json
{
  "status": "accepted",
  "experiment_name": "ssp-gpt4o-20260301T1200"
}
```

## Configuring via DB

### Set webhook URL and default payload
```sql
UPDATE datasets
SET remote_experiment_url = 'https://your-service/api/v1/experiments/trigger',
    remote_experiment_payload = '{"model": "gpt-4o", "item_timeout": 300, "experiment_timeout": 1800, "cache_enabled": false}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

### Read current configuration
```sql
SELECT name, remote_experiment_url,
       remote_experiment_payload::text AS payload
FROM datasets
WHERE project_id = '{PROJECT_ID}'
  AND remote_experiment_url IS NOT NULL;
```

### Clear configuration
```sql
UPDATE datasets
SET remote_experiment_url = NULL,
    remote_experiment_payload = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE project_id = '{PROJECT_ID}'
  AND name = '{DATASET_NAME}';
```

## Configuring via Langfuse UI

1. Navigate to Project → Datasets → Select dataset
2. Click "Start Experiment"
3. Click the `⚡` icon under "Custom Experiment"
4. Enter:
   - **URL**: Your webhook endpoint
   - **Default config**: JSON payload (users can modify per-trigger)
5. Save

## Langfuse Documentation References

- [Remote Dataset Runs](https://langfuse.com/docs/evaluation/dataset-runs/remote-run)
- [Remote Experiment Trigger Changelog](https://langfuse.com/changelog/2025-07-24-remote-experiment-triggers)
