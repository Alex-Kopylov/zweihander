---
name: openapi-inspect
description: >
  This skill should be used when the user wants to explore an endpoint,
  show endpoint details, view endpoint schema, inspect an endpoint,
  understand what an endpoint accepts, or see endpoint input and output.
---

# OpenAPI Endpoint Inspector

Fetch and display full details for a specific API endpoint from a running service's OpenAPI spec.

## Instructions

Use `{host}` as the base URL. Default to `http://localhost:8000` if the user does not specify a host.

### 1. Fetch endpoint details

Pull the endpoint entry from the OpenAPI spec using jq:

```bash
curl -s {host}/openapi.json | jq '.paths["/path/to/endpoint"]'
```

Replace `"/path/to/endpoint"` with the actual path the user asked about.

### 2. Find $ref references

Scan the output for any `"$ref": "#/components/schemas/SchemaName"` entries. Collect every unique schema name.

### 3. Resolve each referenced schema

For each `$ref` found, query the full schema definition:

```bash
curl -s {host}/openapi.json | jq '.components.schemas.SchemaName'
```

Replace `SchemaName` with the actual name extracted from the `$ref`.

If a resolved schema itself contains nested `$ref` entries, resolve those as well until all schemas are fully expanded.

### 4. Present the results

Display to the user:

- HTTP methods available on the endpoint (GET, POST, etc.)
- Request parameters (path, query, header)
- Request body schema (fully resolved, not just the `$ref`)
- Response schemas for each status code (fully resolved)
- Any example values found in the spec
