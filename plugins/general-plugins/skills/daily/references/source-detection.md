# Source Detection

Scan the project root to determine which sources are available. Check each signal below — if it matches, add that source to the active list.

## Detection rules

| Source | Signal | Check |
|--------|--------|-------|
| **git** | `.git/` directory exists | Always present in git repos. Read `references/sources/git.md` |
| **azure-devops** | Git remote contains `dev.azure.com` or `visualstudio.com` | Run `git remote -v` and match the URL pattern |
| **github** | Git remote contains `github.com` | Run `git remote -v` and match the URL pattern |
| **gitlab** | Git remote contains `gitlab.com` or `gitlab.` (self-hosted) | Run `git remote -v` and match the URL pattern |
| **slack** | MCP server named `slack` in `.mcp.json` or `.claude/settings.json` | Check MCP config files |
| **microsoft-teams** | MCP server named `teams` or `microsoft-teams` in MCP config | Check MCP config files |
| **telegram** | MCP server named `telegram` in MCP config | Check MCP config files |
| **custom-mcp** | Any other MCP server that looks like a data/project source | Check MCP config, read `references/sources/custom-mcp.md` for guidance |

## Detection order

1. Check git remote first — this determines the primary platform (Azure DevOps / GitHub / GitLab)
2. Check MCP configs for communication and custom sources
3. Check for platform-specific files (e.g. `azure-pipelines.yml`, `.github/workflows/`)

## Example: Azure DevOps project

Given this remote:
```
origin  git@ssh.dev.azure.com:v3/Cybertorch/NCAI/ai-ssp-generation (fetch)
```

And this `.mcp.json`:
```json
{
  "mcpServers": {
    "azure-devops": { "command": "npx", "args": ["-y", "@azure-devops/mcp", "Cybertorch"] },
    "azure": { "command": "npx", "args": ["-y", "@azure/mcp", "server", "start"] }
  }
}
```

Detected sources: `git`, `azure-devops`

**Extracted context from remote URL:**
- Organization: `Cybertorch`
- Project: `NCAI`
- Repository: `ai-ssp-generation`

These values are passed to the Azure DevOps source for API/MCP calls.

## Example: GitHub project

Given this remote:
```
origin  git@github.com:acme/backend-api.git (fetch)
```

And a `.mcp.json` with a `slack` server configured.

Detected sources: `git`, `github`, `slack`

**Extracted context:**
- Owner: `acme`
- Repository: `backend-api`
