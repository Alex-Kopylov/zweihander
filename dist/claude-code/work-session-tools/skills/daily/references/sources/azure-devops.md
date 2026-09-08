# Source: Azure DevOps

Detected when git remote matches `dev.azure.com` or `visualstudio.com`.

## Context extraction

Parse the remote URL to get organization, project, and repo:

```
git@ssh.dev.azure.com:v3/{org}/{project}/{repo}
https://dev.azure.com/{org}/{project}/_git/{repo}
https://{org}.visualstudio.com/{project}/_git/{repo}
```

## What to fetch

Use the Azure DevOps MCP server if available (`azure-devops` in `.mcp.json`), otherwise fall back to `az devops` CLI.

### Pull Requests

Fetch PRs where the current user is author or reviewer, updated in the last 24h.

**Via MCP:** Use the azure-devops MCP tools to list PRs for the repository, filtering by status (active, completed) and date.

**Via CLI:**
```bash
az repos pr list --org https://dev.azure.com/{org} --project {project} --repository {repo} --status all --top 20
```

For each PR capture: ID, title, source branch, target branch, status, reviewers, vote status.

### PR Comments

For each active PR, fetch recent comment threads:

**Via CLI:**
```bash
az repos pr thread list --org https://dev.azure.com/{org} --id {pr-id}
```

Capture: author, content preview (first ~80 chars), status (active/resolved), timestamp.

### Work Items

Fetch work items assigned to current user or updated recently.

**Via CLI (WIQL query):**
```bash
az boards query --org https://dev.azure.com/{org} --project {project} \
  --wiql "SELECT [Id],[Title],[State],[Changed Date] FROM WorkItems WHERE [Assigned To] = @Me AND [Changed Date] >= @Today - 1 ORDER BY [Changed Date] DESC"
```

For each item capture: ID, title, type (Bug/Task/Story), state, state change direction.

### Work Item Comments

For items with recent activity, fetch comments:

```bash
az boards work-item show --org https://dev.azure.com/{org} --id {item-id} --expand all
```

### Pipeline Runs

Fetch pipeline runs from the last 24h, **scoped to the current repository only**.

Step 1 — List pipelines that belong to this repository:
```bash
az pipelines list --org https://dev.azure.com/{org} --project {project} --repository {repo} --repository-type tfsgit
```

Step 2 — For each pipeline ID returned, fetch recent runs:
```bash
az pipelines runs list --org https://dev.azure.com/{org} --project {project} --pipeline-ids {pipeline-id} --top 5
```

Only include runs from current-repo pipelines; exclude same-project pipelines from other repos (e.g. `other-service` for `my-app`) because they add noise.

Capture: pipeline name, run number, result (succeeded/failed/canceled), branch, timestamp.

## Example output

From the `my-app` repo in the `Acme-Corp/ProjectX` project:

```markdown
## Pull Requests

### Completed
- **PR #42** feat(auth): add OAuth2 support → `develop`
- **PR #38** feat(api): add pagination to list endpoints → `develop`

### Active
- **PR #51** feat(search): full-text search integration — 2 new comments from @reviewer

## Work Items

### Status changes
- **#101** Implement user dashboard: Active → Resolved
- **#108** Add export functionality: New → Active

### Assigned to me
- **#105** API rate limiting (Active)
- **#99** Monitoring dashboard (Active)
```
