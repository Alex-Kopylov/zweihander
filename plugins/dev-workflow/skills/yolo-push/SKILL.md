---
name: yolo-push
description: Run a guarded commit-to-deploy workflow that verifies branch freshness, invokes commit and create-pr, waits for green CI, invokes approve-pr, monitors CD, offers to clean up the merged branch and worktree, and reports final deployment state. Use when the user asks to yolo-push, ship current changes, or execute the full PR-to-deployment flow.
disable-model-invocation: true
---

# YOLO Push

## Invocation Gate

Proceed only when the user explicitly invokes this skill by name using the
harness's direct skill-command syntax. Do not invoke it for generic requests
to commit, push, open a PR, merge, deploy, or ship changes.

## Workflow

Progress:

- [ ] Step 1: Refresh the checkout before evaluating freshness. Run
  `git fetch --all --prune && git pull --ff-only` when the current branch has
  an upstream. If no upstream exists, treat the checkout as a new PR path:
  continue to Step 2, then invoke `dev-workflow:create-pr` after committing;
  do not stop solely because the upstream is missing. Stop only on divergence
  or unknown freshness. If `HEAD` is detached, establish a delivery branch
  before committing because a PR must have a source branch.
- [ ] Step 2: Invoke `dev-workflow:commit` to create atomic commit(s) for the
  current logical changes.
- [ ] Step 3: Check whether the current branch already has an open PR. Reuse
  it if one exists; otherwise invoke `dev-workflow:create-pr` to open one.
- [ ] Step 4: Start babysitting the PR. Drive the remaining steps and continue
  until it is merged or closed. If a non-negotiable failure gate is hit, stop
  and report it with the PR link.
- [ ] Step 5: If no CI is configured, pass the CI gate. Otherwise, wait for CI.
- [ ] Step 6: If configured CI is not green, stop with the failing stages and
  PR link.
- [ ] Step 7: Invoke `dev-workflow:approve-pr`.
- [ ] Step 8: If no CD/deployment is configured, pass the CD gate. Otherwise,
  monitor CD/deployment status until it reaches a terminal state.
- [ ] Step 9: Once the PR is merged and CD reached a terminal state, run
  Post-Merge Cleanup.
- [ ] Step 10: Report the final CD status, deployment URL or environment when
  available, any failed stage logs or links, and the cleanup result.

## Post-Merge Cleanup

Checks what deleting the PR's worktree, local branch, and remote branch would
lose, asks the user once, and deletes only on consent. Examples use GitHub and
reuse shell variables across blocks; substitute resolved values if the shell
does not persist them. `$PR` is the PR from Step 3.

- [ ] Cleanup 1: Resolve PR facts and move to the main worktree, because
  removing the PR worktree deletes the directory the session may be running
  in.

  ```bash
  read -r N BRANCH HEAD STATE < <(gh pr view "$PR" \
    --json number,headRefName,headRefOid,state \
    --jq '[.number,.headRefName,.headRefOid,.state]|@tsv')
  DEFAULT=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
  PROTECTED=$(gh api "repos/{owner}/{repo}/branches/$BRANCH" --jq .protected 2>/dev/null)
  MAIN=$(git worktree list --porcelain | awk 'NR==1{print substr($0,10)}')
  WT=$(git worktree list --porcelain | awk -v b="branch refs/heads/$BRANCH" \
    '/^worktree /{w=substr($0,10)} $0==b{print w}')
  cd "$MAIN"
  echo "Restore point: git branch $BRANCH $HEAD"
  ```

  Skip all cleanup unless `STATE` is `MERGED`, `BRANCH` is not `DEFAULT`, and
  `PROTECTED` is not `true`.

- [ ] Cleanup 2: Check for irreversible losses. These commands only read.

  ```bash
  git fetch -q --prune origin && git fetch -q origin "refs/pull/$N/head"
  echo "Worktree files:"
  [ -n "$WT" ] && [ "$WT" != "$MAIN" ] && git -C "$WT" status --short --ignored
  echo "Local commits missing from the PR:"
  git log --oneline "$HEAD..$BRANCH" -- 2>/dev/null
  echo "Remote commits missing from the PR:"
  git log --oneline "$HEAD..origin/$BRANCH" -- 2>/dev/null
  echo "Open PRs based on the branch:"
  gh pr list --base "$BRANCH" --state open --json url --jq '.[].url'
  ```

  Only ignored files (`!!`) are lost irreversibly on delete. Modified or
  untracked files keep the worktree, missing local commits keep the local
  branch, and missing remote commits or based PRs keep the remote branch.

- [ ] Cleanup 3: Ask the user exactly one question that lists the findings,
  with two options:

  - `Delete the merged branch locally, on the remote, and its worktree if any`
  - `Keep everything for now`

  On keep, touch nothing and report `Cleanup: kept by user`. Skip the question
  when nothing is left to delete.

- [ ] Cleanup 4: On delete, run the guarded deletions. The guards re-check
  state, so anything that appeared after the question is kept too.
  `git branch -d` rejects squash and rebase merges; the ancestor check
  replaces it.

  ```bash
  if [ "$WT" = "$MAIN" ]; then git switch "$DEFAULT" && git pull --ff-only
  elif [ -n "$WT" ]; then git worktree remove "$WT"; fi
  if ! git show-ref -q --verify "refs/heads/$BRANCH"; then echo "Local: already gone"
  elif git merge-base --is-ancestor "$BRANCH" "$HEAD"; then git branch -D "$BRANCH"
  else echo "Local: kept, has commits not in the PR"; fi
  if [ -n "$(gh pr list --base "$BRANCH" --state open --json number --jq '.[].number')" ]; then
    echo "Remote: kept, open PRs target it"
  elif git ls-remote -q --exit-code --heads origin "$BRANCH" >/dev/null; then
    git push origin --delete "$BRANCH" --force-with-lease="refs/heads/$BRANCH:$HEAD"
  fi
  git fetch -q --prune origin
  ```

## Non-Negotiable Stops

- Approve only when CI is green or not configured.
- Do not bypass, override, retry-loop indefinitely, or reinterpret red CI as
  acceptable.
- Do not ask for confirmation to continue past red or unknown CI.
- Do not claim shipped until CD reaches a clear success state when CD is
  configured; otherwise report CD as not configured.
- Delete nothing after the merge unless the user picks the cleanup delete
  option; even then, never pass `--force` to `git worktree remove` or skip a
  cleanup guard.

## Reporting

Use terse status updates:

- `Committed: <sha>`
- `PR: <url>`
- `CI: waiting | green | not configured | failed <stage>`
- `Merge: merged | stopped`
- `CD: waiting | succeeded <environment> | not configured | failed <stage>`
- `Cleanup: kept by user | worktree|local|remote removed or kept <reason>; restore: git branch <branch> <sha>`
