---
name: openapi-list
description: >
  This skill should be used when the user wants to list API endpoints, show endpoints,
  see what endpoints are available, list API routes, or show the API of a running service.
  Trigger phrases: "list endpoints", "show endpoints", "what endpoints are available",
  "list API routes", "show API".
---

# List OpenAPI Endpoints

Fetch the OpenAPI spec from a running service and list all endpoints with their HTTP methods and summaries.

## Instructions

1. Determine the host. If the user provides a host URL, use it. Otherwise default to `http://localhost:8000`.
2. Run the following command, replacing `{host}` with the resolved host:

```bash
curl -s {host}/openapi.json | jq -r '.paths | to_entries[] | .key as $path | .value | to_entries[] | "\(.key | ascii_upcase) \($path)  \(.value.summary // "")"'
```

3. Present the output to the user as-is. If the command fails, report that the service may not be running or the OpenAPI spec is not available at the expected path.
