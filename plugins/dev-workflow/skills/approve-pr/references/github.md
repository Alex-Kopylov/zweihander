# GitHub

```sh
gh pr view "$pr" --json number,state,isDraft,baseRefName,headRefOid,mergeStateStatus,reviewDecision,statusCheckRollup,url
gh pr checks "$pr" --required --watch --fail-fast && gh pr review "$pr" --approve
HEAD=$(gh pr view "$pr" --json headRefOid --jq .headRefOid); gh pr merge "$pr" --match-head-commit "$HEAD" --merge
```

