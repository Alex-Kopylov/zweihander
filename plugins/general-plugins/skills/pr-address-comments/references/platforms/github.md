# GitHub — PR Review Comments

## Finding PRs for Current Branch

```bash
gh pr view --json number,title,url,headRefName,baseRefName,state,reviewDecision
```

If no PR exists for the current branch, `gh pr view` exits with an error — ask the user for the PR link or number.

Alternatively, search by branch:

```bash
gh pr list --head "$(git branch --show-current)" --state open --json number,title,url
```

## Fetching Review Comments

### All review comments (from formal reviews)

```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/comments --jq '.[] | {id, path, line, body, user: .user.login, created_at, in_reply_to_id}'
```

### Review threads (conversations)

```bash
gh pr view {prNumber} --json reviewThreads --jq '.reviewThreads[] | select(.isResolved == false)'
```

Each thread contains:
- `isResolved` — whether the thread is resolved
- `path` — file path
- `line` — line number
- `comments[]` — list of comments (author, body)

### General PR comments (not tied to code)

```bash
gh pr view {prNumber} --json comments --jq '.comments[] | {author: .author.login, body}'
```

## Filtering

Keep only:
- Unresolved threads (`isResolved == false`)
- Comments not authored by the current user

Detect current GitHub user:

```bash
gh api user --jq '.login'
```

## Replying to a Review Comment

```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/comments/{commentId}/replies \
  --method POST \
  --field body="Fixed: {description}"
```

## Resolving a Thread

GitHub resolves threads by GraphQL mutation. Use `gh api graphql`:

```bash
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "{threadNodeId}"}) {
      thread { isResolved }
    }
  }
'
```

To get the `threadNodeId`, fetch threads with node IDs:

```bash
gh api graphql -f query='
  query {
    repository(owner: "{owner}", name: "{repo}") {
      pullRequest(number: {prNumber}) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes { body author { login } }
            }
            path
            line
          }
        }
      }
    }
  }
'
```

## Posting a General Reply

For non-review comments (general PR conversation):

```bash
gh pr comment {prNumber} --body "Fixed: {description}"
```
