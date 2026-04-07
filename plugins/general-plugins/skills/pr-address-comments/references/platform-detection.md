# Platform Detection

## Detecting the Platform

Parse the origin URL or user-provided PR link to determine the platform:

| Pattern in URL | Platform | Details file |
|----------------|----------|--------------|
| `dev.azure.com` or `visualstudio.com` | Azure DevOps | `platforms/azure-devops.md` |
| `github.com` | GitHub | `platforms/github.md` |

If the platform cannot be determined, ask the user via AskUserQuestion.

## Auto-Detecting PR from Current Branch

1. Run `git remote get-url origin` to get the repo URL
2. Determine the platform from the URL pattern above
3. Run `git branch --show-current` to get the current branch name
4. Use the platform-specific PR lookup (see platform files) to find open PRs from this branch
5. If exactly one PR found — use it
6. If multiple — present via AskUserQuestion
7. If none — ask user for the PR link

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
