# Source: GitHub

Detected when git remote matches `github.com`.

## Context extraction

Parse the remote URL:

```
git@github.com:{owner}/{repo}.git
https://github.com/{owner}/{repo}.git
```

## What to fetch

Use `gh` CLI (GitHub CLI). Verify it's installed and authenticated: `gh auth status`.

### Pull Requests

```bash
# PRs authored by me, updated in last 24h
gh pr list --author @me --state all --json number,title,state,baseRefName,updatedAt,reviewDecision

# PRs where I'm requested reviewer
gh pr list --search "review-requested:@me" --json number,title,state,updatedAt
```

### PR Comments & Reviews

For each active PR:
```bash
gh pr view {number} --json reviews,comments,latestReviews
```

### Issues

```bash
# Issues assigned to me
gh issue list --assignee @me --state open --json number,title,state,updatedAt,labels

# Issues I commented on recently
gh issue list --search "commenter:@me sort:updated" --limit 10 --json number,title,state,updatedAt
```

### Workflow Runs (CI/CD)

```bash
gh run list --limit 10 --json databaseId,name,conclusion,headBranch,createdAt,status
```

### Notifications (optional)

```bash
gh api notifications --jq '.[] | {subject: .subject.title, type: .subject.type, reason: .reason, updated_at: .updated_at}'
```

## Example output

```markdown
## Pull Requests

### Created
- **#142** Add rate limiting to API endpoints → `main` (open, review requested)

### Updated
- **#138** Refactor auth middleware — approved by @alice, 1 new comment

### Merged
- **#135** Fix connection pool exhaustion — merged into `main`

## Issues

### Assigned to me
- **#201** Investigate memory leak in worker process (open, bug)
- **#198** Add OpenTelemetry tracing (open, enhancement)

## CI/CD

- **CI** run #456 — succeeded (`main`)
- **CI** run #455 — failed (`feat/rate-limiting`) — test timeout
```
