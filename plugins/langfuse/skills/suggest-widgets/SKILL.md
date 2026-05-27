---
name: suggest-widgets
description: >
  This skill should be used when the user wants recommendations for meaningful
  Langfuse dashboard visualizations based on available data. Trigger phrases
  include "suggest widgets", "recommend visualizations", "what should I
  visualize", "widget suggestions", "dashboard recommendations". It discovers
  available data, analyzes patterns, and proposes relevant widget
  configurations.
---

# Suggest Langfuse Dashboard Widgets

Analyze available Langfuse data -- scores, traces, models, and observations --
and recommend meaningful dashboard visualizations. Present suggestions as a
numbered list, then create selected widgets via the `create-widget` skill.

## Prerequisites

- **Langfuse Host URL** and **Project ID** from the parent plugin context.
- **Database connection** via psycopg2 (preferred) or docker exec psql fallback.
- Python library `psycopg2-binary` installed. If missing, install via
  `uv add psycopg2-binary`.
- The `discover-scores`, `discover-traces`, and `discover-models` skills must
  be available for data enumeration.

## Step-by-Step Procedure

### 1. Establish Time Range

Ask the user for the analysis time range. Common options:

- Last 7 days
- Last 30 days
- Last 90 days
- Custom date range

Default to **last 30 days** if the user does not specify.

### 2. Discover Available Data

Use the discovery skills to enumerate what data exists in the project within
the selected time range. Run these queries in parallel when possible.

#### Discover Scores

Delegate to the `discover-scores` skill, or query directly:

```sql
SELECT DISTINCT name, data_type, source,
       COUNT(*) AS score_count,
       MIN(timestamp) AS first_seen,
       MAX(timestamp) AS last_seen
FROM scores
WHERE project_id = %(project_id)s
  AND timestamp >= NOW() - INTERVAL '%(days)s days'
GROUP BY name, data_type, source
ORDER BY score_count DESC;
```

Capture:
- Which score names exist
- Whether scores are NUMERIC or CATEGORICAL
- Score volume per name
- Score sources (API, ANNOTATION, EVAL)

#### Discover Traces

Delegate to the `discover-traces` skill, or query directly:

```sql
SELECT name, COUNT(*) AS trace_count,
       COUNT(DISTINCT user_id) AS unique_users,
       COUNT(DISTINCT session_id) AS unique_sessions
FROM traces
WHERE project_id = %(project_id)s
  AND timestamp >= NOW() - INTERVAL '%(days)s days'
GROUP BY name
ORDER BY trace_count DESC
LIMIT 20;
```

Capture:
- Trace names and volumes
- Whether user IDs are present
- Whether sessions are present

Also check for tags:

```sql
SELECT DISTINCT unnest(tags) AS tag, COUNT(*) AS tag_count
FROM traces
WHERE project_id = %(project_id)s
  AND timestamp >= NOW() - INTERVAL '%(days)s days'
  AND tags IS NOT NULL AND array_length(tags, 1) > 0
GROUP BY tag
ORDER BY tag_count DESC
LIMIT 20;
```

#### Discover Models

Delegate to the `discover-models` skill, or query directly:

```sql
SELECT model, COUNT(*) AS observation_count,
       SUM(total_cost) AS total_cost,
       AVG(EXTRACT(EPOCH FROM (end_time - start_time))) AS avg_latency,
       SUM(total_tokens) AS total_tokens
FROM observations
WHERE project_id = %(project_id)s
  AND start_time >= NOW() - INTERVAL '%(days)s days'
  AND model IS NOT NULL
GROUP BY model
ORDER BY observation_count DESC
LIMIT 20;
```

Capture:
- Which models are in use
- Cost distribution across models
- Latency characteristics
- Token consumption

### 3. Generate Suggestions Based on Discovered Data

Apply the following rules to generate relevant suggestions. Only suggest
visualizations for data that actually exists.

#### If Numeric Scores Exist

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Average score trend over time | `SCORES_NUMERIC` | `value`, `avg` | `timestampDay` | `LINE_TIME_SERIES` |
| Score comparison across names | `SCORES_NUMERIC` | `value`, `avg` | `name` | `HORIZONTAL_BAR` |
| Score distribution (p50/p95) | `SCORES_NUMERIC` | `value`, `p50` + `p95` | `timestampDay` | `LINE_TIME_SERIES` |
| Score value histogram | `SCORES_NUMERIC` | `value`, `count` | _(none)_ | `HISTOGRAM` |

If multiple score sources exist (e.g., API + EVAL), suggest filtered views per
source.

#### If Categorical Scores Exist

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Category breakdown | `SCORES_CATEGORICAL` | `count`, `count` | `stringValue` | `HORIZONTAL_BAR` |
| Categories over time | `SCORES_CATEGORICAL` | `count`, `count` | `timestampDay` | `BAR_TIME_SERIES` |

#### If Multiple Models Exist

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Cost comparison by model | `OBSERVATIONS` | `totalCost`, `sum` | `providedModelName` | `HORIZONTAL_BAR` |
| Latency comparison by model | `OBSERVATIONS` | `latency`, `avg` | `providedModelName` | `HORIZONTAL_BAR` |
| Cost trend over time | `OBSERVATIONS` | `totalCost`, `sum` | `startTimeMonth` | `LINE_TIME_SERIES` |
| Token usage by model | `OBSERVATIONS` | `totalTokens`, `sum` | `providedModelName` | `PIE` |
| Model usage distribution | `OBSERVATIONS` | `totalCost`, `count` | `providedModelName` | `PIE` |

#### If Trace Tags Exist

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Trace count by tag | `TRACES` | `latency`, `count` | `tags` | `HORIZONTAL_BAR` |

#### If Sessions Exist

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Traces per session trend | `TRACES` | `latency`, `count` | `timestampMonth` | `BAR_TIME_SERIES` |

#### If Multiple Environments Exist

**Note:** Environment data requires the REST API (not the DB fallback). The `environment` column exists only in ClickHouse, not in the Postgres `traces` table. Discover environments via the REST API before suggesting this widget.

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Traces by environment | `TRACES` | `latency`, `count` | `environment` | `PIE` |

#### Always Suggest (Universal)

These are generally useful regardless of data shape:

| Suggestion | View | Metric | Dimension | Chart Type |
|---|---|---|---|---|
| Total cost (big number) | `OBSERVATIONS` | `totalCost`, `sum` | _(none)_ | `NUMBER` |
| Trace volume over time | `TRACES` | `latency`, `count` | `timestampMonth` | `BAR_TIME_SERIES` |
| Latency p95 over time | `OBSERVATIONS` | `latency`, `p95` | `startTimeMonth` | `LINE_TIME_SERIES` |

### 4. Present Suggestions

Format suggestions as a numbered list with clear descriptions:

```
Based on your data from the last 30 days, here are recommended widgets:

 1. Average Score Trend -- Line chart showing avg score value over time
    (3 numeric scores found: accuracy, relevance, completeness)

 2. Cost by Model -- Horizontal bar chart comparing total cost across models
    (4 models found: gpt-4o, gpt-4o-mini, model-a, model-b)

 3. Latency P95 Over Time -- Line chart tracking 95th percentile latency daily

 4. Trace Volume -- Bar chart showing daily trace count
    (12,450 traces in period)

 5. Total Cost (Big Number) -- Single stat showing aggregate cost
    ($142.37 total in period)

Which widgets would you like to create? Enter numbers (e.g., "1, 3, 5") or "all".
```

Include data context (counts, model names, score names) to help the user make
informed selections.

### 5. Create Selected Widgets

For each selection, delegate to the `create-widget` skill with the
pre-computed configuration. Pass all parameters:

- `name` -- descriptive widget name
- `description` -- brief explanation of what the widget shows
- `view` -- from the suggestion table
- `dimensions` -- from the suggestion table
- `metrics` -- from the suggestion table
- `chart_type` -- from the suggestion table
- `chart_config` -- appropriate for the chart type
- `filters` -- any relevant filters (e.g., score name prefix)

### 6. Optionally Create a Dashboard

After creating widgets, offer to create a new dashboard and add all the new
widgets to it. If the user agrees, delegate to `manage-dashboard` for dashboard
creation and `layout-widgets` for automatic grid positioning.

## Suggestion Priority

When many suggestions are possible, prioritize by:

1. **Scores** -- most directly actionable for evaluation workflows
2. **Cost metrics** -- critical for budget monitoring
3. **Latency metrics** -- important for performance tracking
4. **Volume metrics** -- useful for usage monitoring
5. **Breakdowns** (by model, environment, tag) -- useful for comparison

Limit suggestions to a maximum of **10** to avoid overwhelming the user. Select
the most impactful based on data volume and diversity.
