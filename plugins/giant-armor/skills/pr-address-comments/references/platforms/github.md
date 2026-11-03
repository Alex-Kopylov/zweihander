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

## Fetching Review Threads

`gh pr view --json` has no review-thread field; use GraphQL:

```bash
gh api graphql --paginate \
  -f owner='{owner}' -f repo='{repo}' -F pr={prNumber} \
  -f query='
    query($owner: String!, $repo: String!, $pr: Int!, $endCursor: String) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $pr) {
          reviewThreads(first: 100, after: $endCursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              isResolved
              path
              line
              comments(first: 100) {
                nodes { databaseId author { login } body createdAt }
              }
            }
          }
        }
      }
    }
  ' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)'
```

Each thread carries:
- `id` — thread node ID, used to resolve the thread
- `path`, `line` — file and line
- `comments.nodes[]` — every comment; the first one's `databaseId` is the reply target

### General PR comments (not tied to code)

```bash
gh pr view {prNumber} --json comments --jq '.comments[] | {author: .author.login, body, createdAt}'
```

## Filtering

Keep only:
- Unresolved threads (`isResolved == false`)
- Comments not authored by the current user, except AI reviews posted under that login

Detect current GitHub user:

```bash
gh api user --jq '.login'
```

## Replying to a Review Thread

Write the reply as JSON, `{"body": "Fixed in <sha>: <description>"}`, to a file in the run directory, then send the file:

```bash
gh api repos/{owner}/{repo}/pulls/{prNumber}/comments/{commentId}/replies \
  --method POST \
  --input {runDir}/reply.json
```

`{commentId}` is the `databaseId` of the thread's first comment.

## Resolving a Thread

```bash
gh api graphql -f threadId='{threadNodeId}' -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { isResolved }
    }
  }
'
```

## Posting a General Reply

For non-review comments (general PR conversation), write the reply to a file in the run directory:

```bash
gh pr comment {prNumber} --body-file {runDir}/reply.md
```
