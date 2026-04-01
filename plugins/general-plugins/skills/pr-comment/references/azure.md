# Azure DevOps PR Comments

## Parsing Azure DevOps PR URLs

URL formats:
- `https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{prId}`
- `https://{org}.visualstudio.com/{project}/_git/{repo}/pullrequest/{prId}`

Extract: org, project, repo name, PR ID.

You also need the **repository UUID**. Get it via MCP:
```
mcp__azure-devops__repo_get_repo_by_name_or_id(project="{project}", repositoryNameOrId="{repo}")
```

## Finding PRs for Current Branch (MCP)

```
mcp__azure-devops__repo_list_pull_requests_by_repo_or_project(
    repositoryId="{repoUUID}",
    sourceRefName="refs/heads/{branch-name}",
    status="Active"
)
```

## Posting a General Comment (MCP)

```
mcp__azure-devops__repo_create_pull_request_thread(
    repositoryId="{repoUUID}",
    pullRequestId={prId},
    content="Your review message here\n\n---\n_Co-Authored by AI Reviewer_"
)
```

## Posting an Inline Comment (MCP)

```
mcp__azure-devops__repo_create_pull_request_thread(
    repositoryId="{repoUUID}",
    pullRequestId={prId},
    content="Your inline comment\n\n---\n_Co-Authored by AI Reviewer_",
    filePath="/src/example/file.py",
    rightFileStartLine=10,
    rightFileStartOffset=1,
    rightFileEndLine=15,
    rightFileEndOffset=1
)
```

- `filePath` — path relative to repo root, prefixed with `/`
- `rightFileStartLine` / `rightFileEndLine` — line range in the **new version** of the file
- **Offsets are required**: always set `rightFileStartOffset=1` and `rightFileEndOffset=1` (the API rejects calls with line but no offset)
- If commenting on a single line, set start and end line+offset to the same values
- If no lines specified but filePath is given, omit all line/offset params for a file-level comment

## CLI Fallback (az devops)

Use when MCP tools are unavailable.

### General comment

```bash
az repos pr comment create \
  --id {prId} \
  --content "Your review message here

---
_Co-Authored by AI Reviewer_" \
  --org "https://dev.azure.com/{org}" \
  --project "{project}"
```

### Finding PRs for current branch

```bash
az repos pr list \
  --repository "{repo}" \
  --source-branch "$(git branch --show-current)" \
  --status active \
  --org "https://dev.azure.com/{org}" \
  --project "{project}" \
  --output table
```

### Inline comment (CLI limitation)

The `az repos pr comment create` CLI does **not** natively support inline/file-level comments. For inline comments, prefer MCP tools. If MCP is unavailable, use the REST API directly:

```bash
az rest --method post \
  --uri "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repoUUID}/pullRequests/{prId}/threads?api-version=7.1" \
  --body '{
    "comments": [{"content": "Your comment\n\n---\n_Co-Authored by AI Reviewer_", "commentType": 1}],
    "threadContext": {
      "filePath": "/src/example/file.py",
      "rightFileStart": {"line": 10, "offset": 1},
      "rightFileEnd": {"line": 15, "offset": 1}
    },
    "status": 1
  }'
```

## Tool Selection Logic

1. Check if `mcp__azure-devops__repo_create_pull_request_thread` is available — **prefer MCP**
2. If MCP unavailable, check if `az` CLI is installed (`az --version`)
3. For inline comments specifically, MCP is strongly preferred since the CLI lacks native support
