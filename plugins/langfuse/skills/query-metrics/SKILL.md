---
name: query-metrics
description: >-
  This skill should be used when the user wants to query metrics from Langfuse,
  run a metrics query, aggregate data, hit the v1 metrics API, or retrieve
  analytics data from Langfuse. Trigger phrases include "query metrics",
  "run metrics query", "metrics API", "v1 metrics", and "aggregate data".
---

# Query Metrics via Langfuse v1 Metrics API

Execute queries against the Langfuse v1 metrics REST endpoint to retrieve aggregated analytics data. This skill handles the full lifecycle: constructing the query JSON, URL-encoding it, sending the HTTP request, and interpreting the response.

## Endpoint

```
GET /api/public/metrics?query={URL_ENCODED_JSON_STRING}
```

Authentication uses HTTP Basic with the Langfuse public key as username and secret key as password.

## Query Construction

Build a query JSON object with the following top-level fields:

- **view** -- the data source to query against (e.g., `"traces"`, `"observations"`, `"scores-numeric"`, `"scores-categorical"`)
- **dimensions** -- an array of dimension objects specifying how to group results
- **metrics** -- an array of metric objects specifying what to measure and how to aggregate
- **filters** -- an array of filter objects to narrow the result set
- **timeDimension** -- optional object to bucket results by time granularity
- **fromTimestamp** / **toTimestamp** -- ISO 8601 timestamps bounding the query window
- **orderBy** -- optional array controlling result ordering

Refer to `references/v1-metrics-schema.md` for the complete list of valid views, dimension fields, metric fields, aggregation functions, filter columns, filter operators, and filter types.

## Execution via curl

Send the query using curl with Basic Auth. URL-encode the JSON query string using Python's `urllib.parse.quote`:

```bash
curl -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/metrics?query=$(python3 -c "import urllib.parse, json; print(urllib.parse.quote(json.dumps(QUERY_JSON)))")"
```

Replace `QUERY_JSON` with the actual Python dict literal or load it from a variable. For example, to query average latency of observations grouped by model over the last 7 days:

```bash
QUERY='{
  "view": "observations",
  "dimensions": [{"field": "providedModelName"}],
  "metrics": [{"measure": "latency", "aggregation": "avg"}],
  "filters": [],
  "fromTimestamp": "2026-02-21T00:00:00Z",
  "toTimestamp": "2026-02-28T23:59:59Z"
}'

curl -s -u "$PUBLIC_KEY:$SECRET_KEY" \
  "$HOST/api/public/metrics?query=$(python3 -c "import urllib.parse, json; print(urllib.parse.quote(json.dumps(json.loads('''$QUERY'''))))")"
```

Alternatively, construct and execute the request entirely within a Python script for better JSON handling and error reporting:

```python
import json
import urllib.parse
import urllib.request
import base64

query = {
    "view": "observations",
    "dimensions": [{"field": "providedModelName"}],
    "metrics": [{"measure": "latency", "aggregation": "avg"}],
    "filters": [],
    "fromTimestamp": "2026-02-21T00:00:00Z",
    "toTimestamp": "2026-02-28T23:59:59Z",
}

encoded_query = urllib.parse.quote(json.dumps(query))
url = f"{HOST}/api/public/metrics?query={encoded_query}"
credentials = base64.b64encode(f"{PUBLIC_KEY}:{SECRET_KEY}".encode()).decode()

req = urllib.request.Request(url, headers={"Authorization": f"Basic {credentials}"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(json.dumps(data, indent=2))
```

## Building Queries Step by Step

1. **Choose the view.** Determine whether the data lives in traces, observations, numeric scores, or categorical scores. Consult `references/v1-metrics-schema.md` for valid view names.

2. **Select dimensions.** Pick grouping fields appropriate for the chosen view. Each dimension is an object with a `"field"` key. Omit dimensions entirely to get a single aggregate row.

3. **Select metrics.** Pick one or more measures with their aggregation function. Each metric is an object with `"measure"` and `"aggregation"` keys. Available aggregations include `avg`, `sum`, `count`, `min`, `max`, `p50`, `p75`, `p90`, `p95`, `p99`, `histogram`, `uniq` -- but not all aggregations apply to all measures. Check the schema reference.

4. **Apply filters.** Narrow the result set by adding filter objects. Each filter has `"column"`, `"operator"`, `"value"`, and `"type"` keys. Use `references/v1-metrics-schema.md` to find valid filter columns and operators for the chosen view.

5. **Set time bounds.** Provide `fromTimestamp` and `toTimestamp` in ISO 8601 format (these are required). If querying a time series, also set `timeDimension` with the desired `granularity` (`"auto"`, `"minute"`, `"hour"`, `"day"`, or `"month"`).

6. **Set ordering.** Optionally add `orderBy` entries to sort results by a specific field in ascending or descending direction.

## Common Query Patterns

### Average score value over time (daily)

```json
{
  "view": "scores-numeric",
  "dimensions": [{"field": "name"}],
  "metrics": [{"measure": "value", "aggregation": "avg"}],
  "filters": [],
  "timeDimension": {"granularity": "day"},
  "fromTimestamp": "2026-02-01T00:00:00Z",
  "toTimestamp": "2026-02-28T23:59:59Z"
}
```

### Total cost by model

```json
{
  "view": "observations",
  "dimensions": [{"field": "providedModelName"}],
  "metrics": [{"measure": "totalCost", "aggregation": "sum"}],
  "filters": [],
  "fromTimestamp": "2026-02-01T00:00:00Z",
  "toTimestamp": "2026-02-28T23:59:59Z",
  "orderBy": [{"field": "totalCost", "direction": "desc"}]
}
```

### P95 latency for a specific trace name

```json
{
  "view": "traces",
  "dimensions": [],
  "metrics": [{"measure": "latency", "aggregation": "p95"}],
  "filters": [
    {"column": "name", "operator": "=", "value": "my-pipeline", "type": "string"}
  ],
  "timeDimension": {"granularity": "day"},
  "fromTimestamp": "2026-02-01T00:00:00Z",
  "toTimestamp": "2026-02-28T23:59:59Z"
}
```

### Categorical score breakdown

```json
{
  "view": "scores-categorical",
  "dimensions": [{"field": "name"}, {"field": "stringValue"}],
  "metrics": [{"measure": "count", "aggregation": "count"}],
  "filters": [],
  "fromTimestamp": "2026-02-01T00:00:00Z",
  "toTimestamp": "2026-02-28T23:59:59Z"
}
```

## Response Handling

The API returns a JSON object. Parse the response and present results in a readable table format. If the response is empty or contains an error, report the issue clearly -- check that the view, dimensions, metrics, and filters are all valid according to the schema reference.

## Error Troubleshooting

- **401 Unauthorized**: Verify the public key and secret key are correct and belong to the target project.
- **400 Bad Request**: The query JSON is malformed or contains invalid field names. Cross-check every field against `references/v1-metrics-schema.md`.
- **Empty results**: The time range may not contain data, or filters may be too restrictive. Widen the time window or relax filters.
- **URL encoding issues**: Ensure the entire JSON string is properly URL-encoded. Use Python's `urllib.parse.quote` rather than manual encoding.
