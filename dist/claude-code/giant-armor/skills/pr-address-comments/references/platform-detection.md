# Platform Detection

## Detecting the Platform

Determine the platform from the origin URL or PR link:

| Pattern in URL | Platform | Details file |
|----------------|----------|--------------|
| `dev.azure.com` or `visualstudio.com` | Azure DevOps | `platforms/azure-devops.md` |
| `github.com` | GitHub | `platforms/github.md` |

If the platform cannot be determined, ask the user.

## Auto-Detecting PR from Current Branch

1. Run `git remote get-url origin`
2. Determine the platform from the URL pattern above
3. Run `git branch --show-current`
4. Use the platform-specific PR lookup (see platform files) to find open PRs from this branch
5. If exactly one PR found — use it
6. If multiple — ask the user to choose one
7. If none — ask for the PR link

## Parsing PR URLs

### Azure DevOps

```
https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{prId}
https://{org}.visualstudio.com/{project}/_git/{repo}/pullrequest/{prId}
```

Extract: org, project, repo name, PR ID.

### GitHub

```
https://github.com/{owner}/{repo}/pull/{prNumber}
```

Extract: owner, repo, PR number.
