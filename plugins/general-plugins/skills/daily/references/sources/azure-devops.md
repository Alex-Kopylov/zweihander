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

Fetch pipeline runs from the last 24h:

```bash
az pipelines runs list --org https://dev.azure.com/{org} --project {project} --top 10
```

Capture: pipeline name, run number, result (succeeded/failed/canceled), branch, timestamp.

## Example output

From the `ai-ssp-generation` repo in the `Cybertorch/NCAI` project:

```markdown
## Pull Requests

### Completed
- **PR #769** feat(pipeline): enhance Azure pipeline for beta tag handling → `develop`
- **PR #762** feat(langfuse): add reusable CLI tool for applying tags to prompts → `develop`

### Active
- **PR #867** feat(rag): RAG components integration — 2 new comments from @reviewer

## Work Items

### Status changes
- **#6731** Executive risk summary: Active → Resolved
- **#6877** Risk technical summary generation: New → Active

### Assigned to me
- **#6852** AI assistant SRCM controls generation (Active)
- **#5799** Benchmarking pipeline (Active)
```
