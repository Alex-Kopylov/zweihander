---
name: approve-pr
description: Use when the user explicitly asks to approve and merge a pull request or merge request.
argument-hint: "pr=<url-or-number> [target_branch=<branch>]"
metadata:
  gitlab: references/gitlab.md
  github: references/github.md
  azure_devops: references/azure_devops.md
  bitbucket: references/bitbucket.md
---

# Approve PR

Approve and merge only after the current platform state proves the PR is
merge-ready. Never rely on stale CI, yesterday's pipeline, or a user's memory of
status.

## Arguments

| Argument | Required | Description |
|---|---|---|
| `pr` | Yes | PR/MR URL or number. A number requires the current git remote. |
| `target_branch` | No | Expected destination branch. Stop if the PR targets any other branch. |

## Hard Stops

Stop before approval or merge when any item is true:

- `pr` cannot resolve to exactly one open PR/MR.
- `target_branch` is supplied and does not match the PR target.
- The PR is closed, merged, draft/WIP, conflicted, or not mergeable.
- Required checks, pipelines, policies, or status contexts are failed, pending,
  missing, unknown, stale, or not tied to the current head SHA.
- Blocking discussions, unresolved requested changes, or required approvals
  remain after your approval.
- The merge requires force, admin override, bypass, or a missing head/SHA guard
  where the platform supports one.

Fail loudly: report the exact blocking check, policy, discussion, review, or
branch mismatch. Do not bypass protections.

## Workflow

Progress:

- [ ] Step 1: Resolve platform from `pr` URL. If `pr` is only a number, resolve
  from `git remote get-url origin`.
- [ ] Step 2: Load the matching platform reference from skill `metadata`.
- [ ] Step 3: Fetch PR metadata and record current head SHA.
- [ ] Step 4: Show the actual target branch. If `target_branch` was supplied,
  compare it before approval and treat a mismatch as a hard stop.
- [ ] Step 5: Approve the PR.
- [ ] Step 6: Re-fetch review, approval, check, and mergeability state.
- [ ] Step 7: Merge with a head/SHA guard when available. Use the repository's
  configured merge behavior unless the user specified a merge method.
- [ ] Step 8: Verify final merged state and report the PR URL, target branch,
  merge commit or equivalent ID, and any CD/deploy signal already visible.

## Common Mistakes

| Mistake | Correct behavior |
|---|---|
| Merging because CI "passed earlier" | Re-check current required checks on the current head SHA. |
| Ignoring `target_branch` | Treat a mismatch as a hard stop. |
| Approving then merging immediately | Re-read approval and mergeability after the vote. |
| Bypassing branch policies | Stop and report the required policy instead. |
