# Source: Custom MCP Servers

Detected when MCP config contains servers that don't match any known source but appear to be project-relevant data sources.

## How to identify

Check `.mcp.json` or `.claude/settings.json` for MCP servers. Skip servers that are clearly tooling (formatters, linters, file managers). Look for servers that might provide:
- Wiki or documentation content (Confluence, Notion, custom wikis)
- Project management data (Jira, Linear, Asana, Shortcut)
- Monitoring and observability (Grafana, Datadog, PagerDuty)
- Cloud resource status (AWS, Azure, GCP management MCPs)
- Custom internal tools

## How to fetch

1. List the MCP server's available tools to understand its capabilities
2. Look for tools that list/search/fetch recent items (e.g. `list_pages`, `search_issues`, `get_alerts`)
3. Use date-filtered queries where supported
4. If the server provides a `search` tool, search for the project/repo name

## What to capture

For each custom source:
- Source name (the MCP server name)
- Items created or updated in the last 24h
- Brief summary of each item (title + status if available)

## Example: Confluence wiki MCP

```markdown
## Wiki

### Confluence
- **"SSP Generation Architecture"** — updated by @alice (added sequence diagram for risk reporting flow)
- **"Q1 Roadmap"** — updated by @pm-lead (marked executive risk summary as complete)
```

## Example: Jira MCP

```markdown
## Tasks

### Jira
- **SSP-142** Implement catalog caching: In Progress → Code Review
- **SSP-138** Fix Redis connection pooling: Code Review → Done
- **SSP-145** Add OpenTelemetry spans to LLM calls: Backlog → In Progress (assigned to @jhon)
```

## Example: Grafana MCP

```markdown
## Monitoring

### Grafana
- **api-latency** dashboard: p99 latency spike to 2.3s at 14:00 UTC (normally ~800ms), recovered by 14:30
- No active alerts
```

## Notes

- Custom MCPs vary wildly — probe available tools first, then decide what to fetch
- If a server has too many tools or unclear naming, skip it and note in the daily that it was detected but not queried
- This is the primary extension point — new sources added as custom MCPs are automatically picked up by the detection step
