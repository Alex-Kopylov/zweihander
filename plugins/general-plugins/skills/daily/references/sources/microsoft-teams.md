# Source: Microsoft Teams

Detected when an MCP server named `teams` or `microsoft-teams` is configured.

## What to fetch

Use the Teams MCP tools to access channel messages and chats.

### Relevant channels

Determine which Teams channels matter by checking:
1. Channels in a Team that matches the project/org name
2. Channels explicitly referenced in project docs
3. Channels the user points to when asked

### Channel messages

Fetch messages from relevant channels for the last 24h. For each message capture:
- Team and channel name
- Author
- Content preview (first ~100 chars)
- Reply count
- Mentions (if current user was @mentioned)

### Replies in threads

Summarize threaded discussions — topic and outcome, not individual replies.

### Chats

Skip private 1:1 chats by default. Group chats are included only if they match the project context.

## Example output

```markdown
## Messages

### Microsoft Teams

- **ProjectX > General** — @pm-lead: "Sprint review moved to Thursday 3pm, updated the calendar invite" (2 replies)
- **ProjectX > Dev** — @dev: "Merged the auth refactor PR, deploying to QA now"
- **ProjectX > Dev** — @alice: "QA environment is having Redis connectivity issues, investigating"
```

## Notes

- Teams MCP servers typically use Microsoft Graph API under the hood
- Message formatting may include adaptive cards — extract the plain text content
- If the MCP server supports `/me/messages` or activity feed, use it to find mentions
