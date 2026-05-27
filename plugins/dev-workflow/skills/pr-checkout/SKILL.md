---
name: pr-checkout
description: Switch to PR branch from your platform. Activate when user provides a PR — ID, number, or URL — and wants to checkout/switch/review that branch.
---

# Switch to PR Branch

## Instructions

1. **Parse PR input**
   - Accept PR ID, number, or URL (any platform format)
   - Use `<platform-cli>` to fetch PR metadata and extract the branch name

2. **Extract branch name**
   - Get the head branch from PR metadata via `<platform-cli>`
   - Strip `refs/heads/` prefix if present

3. **Check local changes**

   ```bash
   git status --porcelain
   ```

4. **Handle changes** (if output non-empty)
   - Ask user: "Discard" or "Stash"
   - Discard: `git checkout -- . && git clean -fd`
   - Stash: `git stash -u -m "Auto-stash before PR checkout"`

5. **Checkout branch**

   Primary (worktree):
   ```bash
   wt switch -b develop -c <branch>
   ```

   Fallback (review-only):
   ```bash
   git fetch origin
   git checkout <branch> || git checkout -b <branch> origin/<branch>
   ```

## Example

**Input:** PR #42

**Steps:**

1. Fetch PR metadata via `<platform-cli>` → branch: `feat/42-add-feature`
2. Check changes → stash if needed
3. Checkout: `wt switch -b develop -c feat/42-add-feature`
