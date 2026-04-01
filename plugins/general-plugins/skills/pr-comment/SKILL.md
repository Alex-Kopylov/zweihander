---
name: pr-comment
description: Post a review comment to a pull request. Use whenever the user asks to "post a comment", "add review comment", "comment on PR", "leave feedback on PR", "post inline comment", "add PR note", "review comment", or wants to post any kind of feedback to a pull request. Handles both general PR comments and inline file-specific comments. Works with Azure DevOps (via MCP or CLI). If no PR link is given, auto-detects from the current branch.
allowed-tools: Bash, AskUserQuestion, Read, mcp__azure-devops__repo_create_pull_request_thread, mcp__azure-devops__repo_list_pull_requests_by_repo_or_project, mcp__azure-devops__repo_get_pull_request_by_id
---

# PR Comment

Post review comments to pull requests — general or inline on specific lines.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| PR link or ID | No | URL or numeric ID of the PR. Auto-detected if omitted. |
| Comment text | Yes | The review message to post |
| File path | No | Path to file for inline comment |
| Start line | No | First line of the comment range |
| End line | No | Last line of the comment range (defaults to start line) |

## Workflow

### 1. Resolve the PR

**If a PR link/URL is provided**, parse it to extract:
- Platform (Azure DevOps, GitHub, etc.)
- Org, project, repo, and PR ID

**If no PR link is provided**:
1. Run `git remote get-url origin` to identify the platform and repo
2. Run `git branch --show-current` to get the current branch name
3. Search for open PRs from this branch (see `references/azure.md` for platform-specific lookup)
4. If exactly one PR is found — use it
5. If multiple PRs are found — present the list via AskUserQuestion and let the user pick
6. If no PR is found — ask the user for the PR link

### 2. Compose the comment

Take the user's message and append the signature:

```
{user's comment text}

---
_Co-Authored by AI Reviewer_
```

### 3. Post the comment

**General comment** (no file path provided):
- Create a new comment thread on the PR with the composed message

**Inline comment** (file path provided):
- Create a comment thread anchored to the file and line range
- If only start line is given, end line = start line
- If neither start nor end line is given but file path is — post a file-level comment

### 4. Confirm

Report back: "Posted comment on PR #{id}" with a link to the PR.

## Platform Detection

Parse the origin URL or PR link to determine the platform:

| Pattern | Platform |
|---------|----------|
| `dev.azure.com` or `visualstudio.com` | Azure DevOps |
| `github.com` | GitHub |
| `gitlab.com` | GitLab |

Use the matching platform's tools/CLI. See `references/azure.md` for Azure DevOps specifics.

If the platform cannot be determined, ask the user.
