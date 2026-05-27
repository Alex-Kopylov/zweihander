# Source: GitLab

Detected when git remote matches `gitlab.com` or a self-hosted `gitlab.` domain.

## Context extraction

Parse the remote URL:

```
git@gitlab.com:{group}/{repo}.git
https://gitlab.com/{group}/{repo}.git
git@gitlab.company.com:{group}/{repo}.git
```

For self-hosted, extract the base URL for API calls.

## What to fetch

Use `glab` CLI (GitLab CLI) if available, otherwise fall back to GitLab REST API via `curl`.

### Merge Requests

```bash
# MRs authored by me
glab mr list --author @me --state all

# MRs where I'm reviewer
glab mr list --reviewer @me
```

### MR Comments & Discussions

```bash
glab mr view {number} --comments
```

### Issues

```bash
# Issues assigned to me
glab issue list --assignee @me --state opened

# Issues I recently interacted with
glab issue list --search "" --sort updated --per-page 10
```

### Pipeline Runs (CI/CD)

```bash
glab ci list --per-page 10
glab ci view {pipeline-id}
```

### API fallback (self-hosted without glab)

```bash
# List MRs
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://{gitlab-host}/api/v4/projects/{project-id}/merge_requests?state=opened&author_username={user}"

# List pipelines
curl --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://{gitlab-host}/api/v4/projects/{project-id}/pipelines?per_page=10"
```

## Example output

```markdown
## Merge Requests

### Created
- **!89** Add SAML SSO support → `main` (open, 2 approvals needed)

### Updated
- **!85** Database migration for tenant isolation — new thread from @devops-lead

### Merged
- **!82** Fix N+1 query in user listing — merged into `main`

## Issues

### Assigned to me
- **#301** Implement RBAC for API endpoints (open)
- **#298** Audit logging for admin actions (open)

## CI/CD

- **Pipeline #1234** — passed (`main`, deploy to staging)
- **Pipeline #1233** — failed (`feat/saml-sso`) — lint error
```
