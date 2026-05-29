# Langfuse v1 Metrics Query Schema Reference

Reference for valid Langfuse v1 metrics API views, dimensions, metrics, filters, and values.

## Endpoint

```
GET /api/public/metrics?query={URL_ENCODED_JSON_STRING}
```

Authentication: HTTP Basic (public_key as username, secret_key as password).

## Query JSON Shape

```json
{
  "view": "traces" | "observations" | "scores-numeric" | "scores-categorical",
  "dimensions": [{ "field": "<dimension_field>" }],
  "metrics": [{ "measure": "<metric_field>", "aggregation": "<aggregation>" }],
  "filters": [{ "column": "<filter_field>", "operator": "<op>", "value": "<val>", "type": "<type>" }],
  "timeDimension": { "granularity": "auto" | "minute" | "hour" | "day" | "month" },
  "fromTimestamp": "ISO8601",
  "toTimestamp": "ISO8601",
  "orderBy": [{ "field": "<field>", "direction": "asc" | "desc" }]
}
```

`fromTimestamp` and `toTimestamp` are required in addition to `view`. A meaningful query also requires at least one metric.

> **Note — `agg` vs `aggregation`:** The database `dashboard_widgets` table stores the aggregation field as `agg`, while the metrics API expects the field name `aggregation`. When reading widget configs from the DB and sending them to the API, map `agg` to `aggregation`.

---

## Views and Their Fields

### OBSERVATIONS view

**View name:** `"observations"`

**Dimensions:**

| Field | Description |
|---|---|
| `name` | Observation name |
| `providedModelName` | LLM model used |
| `level` | Log level (DEBUG, DEFAULT, WARNING, ERROR) |
| `type` | Observation type (GENERATION, SPAN, EVENT) |
| `environment` | Deployment environment |
| `traceName` | Name of the parent trace |
| `traceUserId` | User ID from the parent trace |
| `traceSessionId` | Session ID from the parent trace |
| `traceTags` | Tags from the parent trace |

**Metrics:**

Numeric aggregation set: `avg`, `p50`, `p75`, `p90`, `p95`, `p99`, `count`, `sum`, `min`, `max`, `histogram`, `uniq`.

| Measures | Valid Aggregations |
|---|---|
| `latency`, `totalTokens`, `inputTokens`, `outputTokens`, `inputCost`, `outputCost`, `totalCost`, `timeToFirstToken`, `streamingLatency`, `outputTokensPerSecond`, `tokensPerSecond` | numeric aggregation set |
| `count`, `countScores`, `toolDefinitions`, `toolCalls` | `count` |

**Filters:**

| Column | Applicable Operators | Type |
|---|---|---|
| `name` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `providedModelName` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `level` | `=`, `any of`, `none of` | `string` or `stringOptions` |
| `type` | `=`, `any of`, `none of` | `string` or `stringOptions` |
| `environment` | `=`, `any of`, `none of` | `string` or `stringOptions` |
| `startTime` | `>`, `<`, `>=`, `<=` | `datetime` |
| `metadata` | `=`, `starts with`, `contains`, `does not contain` | `string` |
| `version` | `=`, `starts with`, `contains`, `does not contain` | `string` |

---

### TRACES view

**View name:** `"traces"`

**Dimensions:**

| Field | Description |
|---|---|
| `name` | Trace name |
| `userId` | User ID associated with the trace |
| `sessionId` | Session ID grouping related traces |
| `tags` | Tags applied to the trace |
| `environment` | Deployment environment |

**Metrics:**

Numeric aggregation set: `avg`, `p50`, `p75`, `p90`, `p95`, `p99`, `count`, `sum`, `min`, `max`, `histogram`, `uniq`.

| Measures | Valid Aggregations |
|---|---|
| `latency`, `observationsCount`, `scoresCount`, `totalTokens`, `totalCost` | numeric aggregation set |
| `count`, `uniqueUserIds`, `uniqueSessionIds` | `count` |

**Filters:**

| Column | Applicable Operators | Type |
|---|---|---|
| `name` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `userId` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `sessionId` | `=`, `starts with`, `contains`, `does not contain` | `string` |
| `tags` | `any of`, `none of` | `arrayOptions` |
| `environment` | `=`, `any of`, `none of` | `string` or `stringOptions` |
| `timestamp` | `>`, `<`, `>=`, `<=` | `datetime` |
| `metadata` | `=`, `starts with`, `contains`, `does not contain` | `string` |

---

### SCORES_NUMERIC view

**View name:** `"scores-numeric"`

**Dimensions:**

| Field | Description |
|---|---|
| `name` | Name of the numeric score |
| `traceName` | Name of the trace the score is attached to |
| `userId` | User ID from the parent trace |
| `traceSessionId` | Session ID from the parent trace |
| `traceTags` | Tags from the parent trace |
| `environment` | Deployment environment |

**Metrics:**

| Measure | Valid Aggregations |
|---|---|
| `value` | `avg`, `p50`, `p75`, `p90`, `p95`, `p99`, `count`, `sum`, `min`, `max`, `histogram`, `uniq` |

**Filters:**

| Column | Applicable Operators | Type |
|---|---|---|
| `scoreName` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `timestamp` | `>`, `<`, `>=`, `<=` | `datetime` |
| `source` | `=`, `any of`, `none of` | `string` or `stringOptions` |

---

### SCORES_CATEGORICAL view

**View name:** `"scores-categorical"`

**Dimensions:**

| Field | Description |
|---|---|
| `name` | Name of the categorical score |
| `stringValue` | The categorical label/value |
| `traceName` | Name of the trace the score is attached to |
| `userId` | User ID from the parent trace |
| `environment` | Deployment environment |

**Metrics:**

| Measure | Valid Aggregations |
|---|---|
| `count` | `count` |

**Filters:**

| Column | Applicable Operators | Type |
|---|---|---|
| `scoreName` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `stringValue` | `=`, `starts with`, `contains`, `does not contain`, `any of`, `none of` | `string` or `stringOptions` |
| `timestamp` | `>`, `<`, `>=`, `<=` | `datetime` |
| `source` | `=`, `any of`, `none of` | `string` or `stringOptions` |

---

## Filter Operators Reference

| Operator | Description | Applicable Types |
|---|---|---|
| `=` | Exact match | `string`, `number` |
| `<>` | Not equal | `number` |
| `>` | Greater than | `number`, `datetime` |
| `<` | Less than | `number`, `datetime` |
| `>=` | Greater than or equal | `number`, `datetime` |
| `<=` | Less than or equal | `number`, `datetime` |
| `starts with` | Prefix match | `string` |
| `contains` | Substring match | `string` |
| `does not contain` | Negative substring match | `string` |
| `any of` | Value in list | `stringOptions`, `arrayOptions` |
| `none of` | Value not in list | `stringOptions`, `arrayOptions` |

## Filter Types Reference

| Type | Description | Value Format |
|---|---|---|
| `string` | Single string value | `"value": "some_string"` |
| `number` | Numeric value | `"value": 42` or `"value": 3.14` |
| `datetime` | ISO 8601 timestamp | `"value": "2026-02-28T00:00:00Z"` |
| `stringOptions` | Array of string values (for `any of` / `none of`) | `"value": ["opt1", "opt2"]` |
| `arrayOptions` | Array of values matching array columns (for tags) | `"value": ["tag1", "tag2"]` |

## Time Dimension Granularities

| Granularity | Bucket Size |
|---|---|
| `auto` | Automatically selected based on time range |
| `minute` | 1 minute |
| `hour` | 1 hour |
| `day` | 1 calendar day |
| `month` | 1 calendar month |

When `timeDimension` is set, the response includes a time bucket column alongside the requested dimensions. Omit `timeDimension` to get a single aggregate result (no time bucketing).

## Order By

Each `orderBy` entry requires:

- `field` -- must match a dimension field or metric measure from the query
- `direction` -- `"asc"` or `"desc"`

Multiple `orderBy` entries are applied in order (primary sort, secondary sort, etc.).
