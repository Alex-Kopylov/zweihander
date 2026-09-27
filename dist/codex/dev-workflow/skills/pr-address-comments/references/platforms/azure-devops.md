# Azure DevOps — PR Threads

## Prerequisites

Resolve the **repository UUID** before any thread operations:

```
mcp__azure-devops__repo_get_repo_by_name_or_id(
    project="{project}",
    repositoryNameOrId="{repo}"
)
```

## Finding PRs for Current Branch

### MCP

```
mcp__azure-devops__repo_list_pull_requests_by_repo_or_project(
    repositoryId="{repoUUID}",
    sourceRefName="refs/heads/{branch-name}",
    status="Active"
)
```

### CLI fallback

```bash
az repos pr list \
  --repository "{repo}" \
  --source-branch "$(git branch --show-current)" \
  --status active \
  --org "https://dev.azure.com/{org}" \
  --project "{project}" \
  --output json
```

## Fetching Review Threads

### MCP

```
mcp__azure-devops__repo_list_pull_request_threads(
    repositoryId="{repoUUID}",
    pullRequestId={prId}
)
```

Returns threads with:
- `id` — thread ID
- `status` — 1=Active, 2=Fixed, 3=WontFix, 4=Closed, 5=ByDesign, 6=Pending
- `threadContext.filePath` — file path (if inline comment)
- `threadContext.rightFileStart.line` / `rightFileEnd.line` — line range
- `comments[]` — list of comments in the thread

### Filtering Threads

Keep only threads where:
- `status == 1` (Active)
- `comments[0].commentType == 1` (text comment, not system)
- Thread is not authored by the current user

## Reading Thread Comments

```
mcp__azure-devops__repo_list_pull_request_thread_comments(
    repositoryId="{repoUUID}",
    pullRequestId={prId},
    threadId={threadId}
)
```

## Replying to a Thread

Invoke the `dev-workflow:pr-comment` skill with the PR ID and reply text.

Alternatively, use MCP directly:

```
mcp__azure-devops__repo_reply_to_comment(
    repositoryId="{repoUUID}",
    pullRequestId={prId},
    threadId={threadId},
    content="Fixed: {description}"
)
```

## Resolving a Thread

Set status to `2` (Fixed):

```
mcp__azure-devops__repo_update_pull_request_thread(
    repositoryId="{repoUUID}",
    pullRequestId={prId},
    threadId={threadId},
    status=2
)
```

### Other Status Values

| Status | Value | When to use |
|--------|-------|-------------|
| Fixed | 2 | Code change made to address the comment |
| WontFix | 3 | Intentionally not changing (explain in reply first) |
| Closed | 4 | Comment no longer relevant |
| ByDesign | 5 | Current behavior is intentional |

Always reply before resolving — never silently mark as fixed.

## CLI Fallback (az devops)

### List threads

No direct CLI command — use REST API:

```bash
az rest --method get \
  --uri "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoUUID}/pullRequests/{prId}/threads?api-version=7.1"
```

### Reply to a thread

```bash
az rest --method post \
  --uri "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoUUID}/pullRequests/{prId}/threads/{threadId}/comments?api-version=7.1" \
  --body '{"content": "Fixed: {description}", "commentType": 1}'
```

### Update thread status

```bash
az rest --method patch \
  --uri "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoUUID}/pullRequests/{prId}/threads/{threadId}?api-version=7.1" \
  --body '{"status": 2}'
```
