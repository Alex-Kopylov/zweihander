# Langfuse Domain Knowledge

Shared data model and connection details for all Langfuse plugin agents and skills.

## Data Model

- **Traces**: Top-level units of work. Fields: id, name, userId, sessionId, tags, metadata, environment, timestamps.
- **Observations**: Individual operations within a trace. Types: GENERATION, SPAN, EVENT, AGENT, TOOL, CHAIN, RETRIEVER, EVALUATOR, EMBEDDING, GUARDRAIL. Fields: id, traceId, name, model, level, startTime, endTime, input, output, usage (promptTokens, completionTokens, totalTokens), cost (inputCost, outputCost, totalCost), latency, metadata.
- **Scores**: Evaluation results attached to traces or observations. Types: NUMERIC (float values 0-1 or custom range), CATEGORICAL (string labels), BOOLEAN (true/false values). Fields: id, name, traceId, observationId, value, dataType, source (API, ANNOTATION, EVAL).
- **Sessions**: Groups of related traces. Fields: id, timestamps.
- **Models**: LLM model definitions with pricing. Fields: id, modelName, unit, inputPrice, outputPrice.

## Relationship Diagram

```
Session 1---* Trace 1---* Observation
                |                |
                1---* Score      1---* Score
```

## Database Tables

`traces`, `observations`, `scores`, `trace_sessions`, `models`, `dashboards`, `dashboard_widgets`, `prompts`, `datasets`, `dataset_items`, `dataset_runs`, `dataset_run_items`, `eval_templates`, `job_configurations`

- ID format: CUID (e.g., `clxxxxxxxxxxxxxxxxxxxxxxxxx`). Langfuse uses CUID v1 (`@default(cuid())` in Prisma). This plugin generates IDs with `cuid2`. Both formats are compatible.
- Some IDs (e.g., `dataset_runs`, `dataset_run_items`) use UUID v4 format — both CUID and UUID are accepted.
- All tables have `project_id` column for multi-tenancy

### Dataset & Experiment Tables

**`datasets`** — Evaluation dataset definitions

| Column | Type | Notes |
|--------|------|-------|
| `id` | text PK | CUID format |
| `name` | text | Unique per project |
| `project_id` | text | FK to projects |
| `description` | text | Optional |
| `metadata` | jsonb | Optional |
| `input_schema` | json | Optional JSON Schema for item inputs |
| `expected_output_schema` | json | Optional JSON Schema for item expected outputs |
| `remote_experiment_url` | text | Webhook URL for Custom Experiment trigger |
| `remote_experiment_payload` | jsonb | Default payload sent with webhook |

PK: `(id, project_id)`. Unique: `(project_id, name)`.

**`dataset_items`** — Individual items in a dataset (versioned via `valid_from`/`valid_to`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | text | Item ID (not unique alone — versioned) |
| `dataset_id` | text | FK to datasets |
| `project_id` | text | FK to projects |
| `input` | jsonb | Item input data |
| `expected_output` | jsonb | Expected output for evaluation |
| `metadata` | jsonb | Optional |
| `status` | DatasetStatus | `ACTIVE` or `ARCHIVED` (default: `ACTIVE`) |
| `source_trace_id` | text | Optional link to originating trace |
| `source_observation_id` | text | Optional link to originating observation |
| `is_deleted` | boolean | Soft delete flag (default: `false`) |
| `valid_from` | timestamp | Version start time |
| `valid_to` | timestamp | Version end time (NULL = current version) |

PK: `(id, project_id, valid_from)`. Items are versioned: each update creates a new row with `valid_from = NOW()` and sets `valid_to` on the previous version.

**`dataset_runs`** — Experiment runs against a dataset

| Column | Type | Notes |
|--------|------|-------|
| `id` | text PK | UUID v4 or CUID |
| `name` | text | Run name (unique per dataset) |
| `dataset_id` | text | FK to datasets |
| `project_id` | text | FK to projects |
| `description` | text | Optional |
| `metadata` | jsonb | Optional (model, provider, params, etc.) |

PK: `(id, project_id)`. Unique: `(dataset_id, project_id, name)`.

**`dataset_run_items`** — Per-item results linking runs to traces

| Column | Type | Notes |
|--------|------|-------|
| `id` | text PK | UUID v4 or CUID |
| `dataset_run_id` | text | FK to dataset_runs |
| `dataset_item_id` | text | FK to dataset_items |
| `trace_id` | text | The trace produced by running this item |
| `observation_id` | text | Optional (backwards compat) |
| `project_id` | text | FK to projects |

PK: `(id, project_id)`.

### Dataset & Experiment Relationship Diagram

```
Dataset 1---* DatasetItem      (items in the dataset)
Dataset 1---* DatasetRun       (experiment runs)
DatasetRun 1---* DatasetRunItem (per-item results)
DatasetRunItem *---1 DatasetItem (which item was tested)
DatasetRunItem *---1 Trace      (what the LLM produced)
Trace 1---* Score              (evaluator scores on the trace)
```

## Langfuse REST API (v1, self-hosted compatible)

- Base URL: `{LANGFUSE_HOST}/api/public`
- Auth: HTTP Basic (public_key as username, secret_key as password)
- Endpoints:
  - `/scores`, `/traces`, `/observations`, `/sessions`, `/models`, `/metrics`, `/prompts`
  - `/datasets` — list all (with item IDs and run names inline)
  - `/datasets/{name}` — get single dataset with full items and run names
  - `/datasets/{name}/runs` — list runs for a dataset (with metadata)
  - `/dataset-items?datasetName={name}` — paginated item list
  - `/dataset-run-items?runName={name}&datasetId={id}` — run item details (with traceId)
  - `POST /datasets` — create dataset
  - `POST /dataset-items` — create/upsert item
- **v2 endpoints** (where available): `/v2/datasets` — paginated list without inline items/runs
- **NOT available via REST API** (require direct DB access):
  - Delete items (only archive via API; hard delete requires DB)
  - Get/set `remote_experiment_url` and `remote_experiment_payload` on datasets
  - Complex joins: scores per run item, aggregated experiment results
  - Delete datasets or runs

## Credential Requirements

Each session requires:

1. **Langfuse Host URL** — e.g., `http://localhost:3000` or `https://cloud.langfuse.com`
2. **Langfuse Public Key** — for API authentication
3. **Langfuse Secret Key** — for API authentication
4. **Project ID** — the Langfuse project slug/ID (visible in URL path)
5. **Database connection** — one of:
   - Direct connection string: `postgresql://user:pass@host:port/dbname`
   - Docker container name + DB credentials (for `docker exec` fallback)

Validate credentials by calling `GET {HOST}/api/public/scores?limit=1`.

## Storage Architecture

Langfuse uses a **hybrid storage model**:

- **PostgreSQL** — Metadata and configuration: `datasets`, `dataset_items`, `dataset_runs`, `eval_templates`, `job_configurations`, `dashboards`, `dashboard_widgets`, `prompts`, `models`.
- **ClickHouse** — Analytics and runtime data: `traces`, `observations`, `scores`, `dataset_run_items_rmt` (denormalized run items).

**Key implication:** The Postgres `traces`, `scores`, and `dataset_run_items` tables exist but are **empty**. All runtime/analytics data lives in ClickHouse. The REST API reads from ClickHouse automatically.

**For experiment result analysis (joining run items → traces → scores):**
1. **Prefer REST API** — it reads from ClickHouse transparently.
2. **ClickHouse direct** — via `docker exec langfuse-clickhouse clickhouse-client --query "..."` for complex analysis queries.
3. **Postgres direct** — only for metadata tables (datasets, items, runs, evaluators, widgets).

### ClickHouse `dataset_run_items_rmt` (denormalized)

A denormalized table containing run item data with inline copies of dataset item and run metadata:

| Column | Type | Notes |
|--------|------|-------|
| `id` | String | Run item ID |
| `project_id` | String | |
| `dataset_run_id` | String | |
| `dataset_item_id` | String | |
| `dataset_id` | String | |
| `trace_id` | String | Linked trace |
| `observation_id` | Nullable(String) | |
| `dataset_run_name` | String | Inline copy |
| `dataset_run_metadata` | Map(String, String) | Inline copy |
| `dataset_item_input` | Nullable(String) | Inline copy (ZSTD compressed) |
| `dataset_item_expected_output` | Nullable(String) | Inline copy (ZSTD compressed) |

## DB Connection Strategy

Priority order:

1. **REST API** (preferred for reads): Reads from ClickHouse transparently. Use for traces, scores, run items.
2. **psycopg2 via Python script** (for Postgres writes): parameterized queries, safe for JSON columns. Install if needed: `uv add psycopg2-binary`.
3. **docker exec psql** (Postgres fallback): when DB is only reachable from within Docker container.
4. **docker exec clickhouse-client** (ClickHouse direct): for complex analytics queries not supported by REST API.

## ID Generation

Use the `cuid2` Python library to generate IDs matching Langfuse's format. Install if needed: `uv add cuid2`.
