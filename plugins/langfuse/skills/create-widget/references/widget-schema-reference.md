# Widget Schema Reference

Complete reference for Langfuse dashboard widget configuration. Use this when
constructing or validating widget INSERT/UPDATE payloads.

---

## Chart Types

Enum: `DashboardWidgetChartType`

| Value                | Category    | Description                     |
|----------------------|-------------|---------------------------------|
| `LINE_TIME_SERIES`   | Time series | Line chart over time            |
| `BAR_TIME_SERIES`    | Time series | Bar chart over time             |
| `HORIZONTAL_BAR`     | Aggregate   | Horizontal bar chart            |
| `VERTICAL_BAR`       | Aggregate   | Vertical bar chart              |
| `PIE`                | Aggregate   | Pie chart                       |
| `NUMBER`             | Aggregate   | Single big number               |
| `HISTOGRAM`          | Distribution| Distribution histogram          |
| `PIVOT_TABLE`        | Tabular     | Tabular pivot view              |

---

## Views

Enum: `DashboardWidgetViews`

| Value                 | Description                              |
|-----------------------|------------------------------------------|
| `TRACES`              | Trace-level data                         |
| `OBSERVATIONS`        | Observation-level data (generations etc) |
| `SCORES_NUMERIC`      | Numeric score values                     |
| `SCORES_CATEGORICAL`  | Categorical score labels                 |

---

## Chart Config Shapes

Each `chart_config` JSON object must match the shape for its `chart_type`:

### Time Series Types (LINE_TIME_SERIES, BAR_TIME_SERIES)

```json
{"type": "<CHART_TYPE>"}
```

No additional fields required.

### Aggregate Types (HORIZONTAL_BAR, VERTICAL_BAR, PIE, NUMBER)

```json
{"type": "<CHART_TYPE>", "row_limit": <int, optional, max 1000>}
```

- `row_limit` is optional. When omitted, the server applies a default.

### HORIZONTAL_BAR (additional options)

```json
{
  "type": "HORIZONTAL_BAR",
  "row_limit": <int, optional, max 1000>,
  "show_value_labels": <bool, optional>
}
```

### HISTOGRAM

```json
{
  "type": "HISTOGRAM",
  "bins": <int, 1-100, default 10>
}
```

- `bins` controls bucket count. Must be between 1 and 100 inclusive.

### PIVOT_TABLE

```json
{
  "type": "PIVOT_TABLE",
  "defaultSort": {
    "column": "<column_name>",
    "order": "ASC" | "DESC"
  }
}
```

- `defaultSort` is optional. When provided, both `column` and `order` are
  required.

---

## Dimension Fields by View

### OBSERVATIONS

| Field              | Description                        |
|--------------------|------------------------------------|
| `name`             | Observation name                   |
| `providedModelName`| LLM model identifier               |
| `level`            | Log level (DEBUG, DEFAULT, etc.)   |
| `type`             | Observation type (GENERATION, etc) |
| `environment`      | Deployment environment             |
| `traceName`        | Name of the parent trace           |
| `traceUserId`      | User ID from the parent trace      |
| `traceSessionId`   | Session ID from the parent trace   |
| `traceTags`        | Tags from the parent trace         |
| `startTimeMonth`   | Month-level time bucketing         |

### TRACES

| Field             | Description                        |
|-------------------|------------------------------------|
| `name`            | Trace name                         |
| `userId`          | Associated user ID                 |
| `sessionId`       | Associated session ID              |
| `tags`            | Trace tags                         |
| `environment`     | Deployment environment             |
| `timestampMonth`  | Month-level time bucketing         |

### SCORES_NUMERIC

| Field             | Description                        |
|-------------------|------------------------------------|
| `name`            | Name of the score                  |
| `traceName`       | Name of the parent trace           |
| `userId`          | User ID on the parent trace        |
| `traceSessionId`  | Session ID from the parent trace   |
| `traceTags`       | Tags from the parent trace         |
| `environment`     | Deployment environment             |
| `timestampDay`    | Day-level time bucketing           |
| `timestampMonth`  | Month-level time bucketing         |

### SCORES_CATEGORICAL

| Field             | Description                        |
|-------------------|------------------------------------|
| `name`            | Name of the score                  |
| `stringValue`     | Categorical label value            |
| `traceName`       | Name of the parent trace           |
| `traceSessionId`  | Session ID from the parent trace   |
| `traceTags`       | Tags from the parent trace         |
| `timestampDay`    | Day-level time bucketing           |
| `timestampMonth`  | Month-level time bucketing         |

---

## Metric Fields and Aggregations by View

### OBSERVATIONS

| Metric Field           | Valid Aggregations                                          |
|------------------------|-------------------------------------------------------------|
| `latency`              | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `totalTokens`          | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `inputTokens`          | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `outputTokens`         | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `inputCost`            | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `outputCost`           | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `totalCost`            | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `timeToFirstToken`     | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `count`                | `count`                                                     |
| `streamingLatency`     | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `outputTokensPerSecond`| `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `tokensPerSecond`      | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `countScores`          | `count`                                                     |
| `toolDefinitions`      | `count`                                                     |
| `toolCalls`            | `count`                                                     |

### TRACES

| Metric Field       | Valid Aggregations                                          |
|--------------------|-------------------------------------------------------------|
| `latency`          | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `count`            | `count`                                                     |
| `observationsCount`| `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `scoresCount`      | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `uniqueUserIds`    | `count`                                                     |
| `uniqueSessionIds` | `count`                                                     |
| `totalTokens`      | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |
| `totalCost`        | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |

### SCORES_NUMERIC

| Metric Field | Valid Aggregations                                          |
|--------------|-------------------------------------------------------------|
| `value`      | `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` |

### SCORES_CATEGORICAL

| Metric Field | Valid Aggregations |
|--------------|--------------------|
| `count`      | `count`            |

---

## Filter JSON Shape

Filters are a JSON array. Each filter object:

```json
{
  "type": "string",
  "column": "<column_name>",
  "operator": "<operator>",
  "value": "<value>"
}
```

### Common Filter Operators

| Operator        | Description                    |
|-----------------|--------------------------------|
| `=`             | Exact match                    |
| `starts with`   | Prefix match                   |
| `ends with`     | Suffix match                   |
| `contains`      | Substring match                |
| `does not contain` | Negative substring match    |
| `is null`       | Null check (no value needed)   |
| `is not null`   | Non-null check (no value needed)|

> **Note:** For string negation use `does not contain`; for number negation use `<>`.

### Example Filters

Score name prefix filter:

```json
[{"type": "string", "column": "name", "operator": "starts with", "value": "self_eval:"}]
```

Environment filter:

```json
[{"type": "string", "column": "environment", "operator": "=", "value": "production"}]
```

Multiple filters (AND logic):

```json
[
  {"type": "string", "column": "model", "operator": "contains", "value": "gpt-4"},
  {"type": "string", "column": "environment", "operator": "=", "value": "production"}
]
```

---

## Intent-to-Config Mapping Table

Use this table to translate user intent into widget configuration:

| User Says                      | View               | Metric (field, agg) | Dimension          | Chart Type          |
|--------------------------------|---------------------|---------------------|--------------------|---------------------|
| "average score over time"      | `SCORES_NUMERIC`    | `value`, `avg`      | `timestampDay`/`Month` | `LINE_TIME_SERIES` |
| "score distribution"           | `SCORES_NUMERIC`    | `value`, `avg`      | `name`             | `HORIZONTAL_BAR`    |
| "cost by model"                | `OBSERVATIONS`      | `totalCost`, `sum`  | `providedModelName`| `HORIZONTAL_BAR` or `PIE` |
| "cost over time"               | `OBSERVATIONS`      | `totalCost`, `sum`  | `startTimeMonth`   | `LINE_TIME_SERIES`  |
| "latency by model"             | `OBSERVATIONS`      | `latency`, `avg`    | `providedModelName`| `HORIZONTAL_BAR`    |
| "latency p95 over time"        | `OBSERVATIONS`      | `latency`, `p95`    | `startTimeMonth`   | `LINE_TIME_SERIES`  |
| "token usage over time"        | `OBSERVATIONS`      | `totalTokens`, `sum`| `startTimeMonth`   | `BAR_TIME_SERIES`   |
| "trace count over time"        | `TRACES`            | `latency`, `count`  | `timestampMonth`   | `BAR_TIME_SERIES`   |
| "traces by environment"        | `TRACES`            | `latency`, `count`  | `environment`      | `PIE`               |
| "score categories breakdown"   | `SCORES_CATEGORICAL`| `count`, `count`    | `stringValue`      | `HORIZONTAL_BAR`    |
| "model usage distribution"     | `OBSERVATIONS`      | `totalCost`, `count`| `providedModelName`| `PIE`               |
| "big number: total cost"       | `OBSERVATIONS`      | `totalCost`, `sum`  | _(none)_           | `NUMBER`            |
| "latency histogram"            | `OBSERVATIONS`      | `latency`, `count`  | _(none)_           | `HISTOGRAM`         |

### Notes on the Mapping Table

- For time-series charts, the dimension should be a timestamp bucketing field.
  Use `startTimeMonth` for OBSERVATIONS views and `timestampMonth` for TRACES
  and SCORES views. Default to the month-level bucketing unless the user
  specifies otherwise.
- For `NUMBER` and `HISTOGRAM` chart types, dimensions are typically empty.
- When the user says "by model" or "by environment", use the corresponding
  field as the dimension (e.g. `providedModelName` for observations, `environment`).
- Multiple metrics can be included in a single widget (array of metric objects).
