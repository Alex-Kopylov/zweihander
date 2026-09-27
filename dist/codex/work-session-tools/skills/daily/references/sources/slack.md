# Source: Slack

Detected when an MCP server named `slack` is configured.

## What to fetch

Use Slack MCP tools to access channel messages and threads.

### Relevant channels

Determine which channels matter by checking:
1. Channels explicitly mentioned in README.md, project docs, or the AI agent's instruction files
2. Channels whose name matches the project or repo name
3. Channels the user points to when asked

### Messages

Fetch messages from relevant channels for the last 24h. For each message capture:
- Channel name
- Author
- Content preview (first ~100 chars)
- Thread reply count (if threaded)
- Reactions (if notable — e.g. eyes, checkmark, alert)

### Threads with replies

If a thread has replies within the time window, summarize the thread topic and conclusion (if any), not every individual reply.

### Direct messages

Skip DMs by default — they are private. Only include if the user explicitly asks.

## Example output

```markdown
## Messages

### Slack

- **#ssp-team** — @alice: "The beta deploy passed all smoke tests, ready for QA sign-off" (3 replies, resolved)
- **#ssp-team** — @bob: "Found a regression in the executive risk summary endpoint" (thread ongoing)
- **#devops** — @ci-bot: "Pipeline #769 succeeded for develop branch"
```

## Notes

- Respect channel privacy — only fetch from channels the MCP token has access to
- Summarize threads rather than listing every message
- If the MCP server supports search, use it to find messages mentioning the repo/project name
