# Source: Telegram

Detected when an MCP server named `telegram` is configured.

## What to fetch

Use the Telegram MCP tools to access group messages.

### Relevant groups/channels

Determine which Telegram groups matter by checking:
1. Groups whose name matches the project, team, or org
2. Groups explicitly referenced in project docs
3. Groups the user points to when asked

### Messages

Fetch messages from relevant groups for the last 24h. For each message capture:
- Group/channel name
- Author
- Content preview (first ~100 chars)
- Reply-to context (if it's a reply, what was the original message about)
- Forwarded-from (if the message was forwarded)

### Pinned messages

Check if any messages were pinned within the time window — these are often important announcements.

## Example output

```markdown
## Messages

### Telegram

- **SSP Dev Group** — @john: "Pushed the fix for catalog caching, please review PR #543"
- **SSP Dev Group** — @alice: "Redis is back up in QA, false alarm on the connectivity issue"
- **DevOps Alerts** — pinned: "Scheduled maintenance window Saturday 2am-4am UTC"
```

## Notes

- Telegram groups can be high-volume — focus on messages that mention the project, repo, or team members
- Skip bot messages unless they carry meaningful status updates (deploy bots, CI bots)
- Private chats are excluded by default
