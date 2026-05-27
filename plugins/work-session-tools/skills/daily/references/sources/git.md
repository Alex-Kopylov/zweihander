# Source: Git

Always available when a `.git/` directory exists. This is the foundation — every other source builds on top of it.

## What to fetch

### Recent commits (within time window)

```bash
git log --oneline --after="YYYY-MM-DDT06:00:00" --all --author="$(git config user.name)"
```

Use the 06:00 cutoff from the time window defined in SKILL.md.

For each commit, capture: hash, message, branch, timestamp.

### Current branch status

```bash
git status --short
git diff --stat
```

Unstaged changes, staged changes, untracked files — summarize counts, not individual files (unless very few).

### Branch diff against upstream

```bash
git log --oneline origin/{main-branch}..HEAD
```

How far ahead is the current branch? Are there unpushed commits?

### Worktrees

```bash
git worktree list
```

For each worktree beyond the main one:
- Path and branch name
- Run `git -C {worktree-path} log --oneline -1` for last commit
- Run `git -C {worktree-path} status --short | wc -l` for dirty file count

This is particularly useful for projects with heavy parallel development. Example output:

```
/repos/my-app                                   d57022e [develop]
/repos/my-app.101-user-dashboard                0c1cd32 [101-user-dashboard]
/repos/my-app.feat-add-caching-layer            12a4792 [feat/add-caching-layer]
```

### Recent branch activity

```bash
git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads/ | head -10
```

Which branches were touched recently? Helps identify active work streams.

## Notes

- Always use `--author` filter to scope to the current user's activity
- If the repo has many worktrees (10+), group them by status: active (commits today), stale (no recent activity), dirty (uncommitted changes)
- Git data is always local and fast — fetch it first, before network sources
