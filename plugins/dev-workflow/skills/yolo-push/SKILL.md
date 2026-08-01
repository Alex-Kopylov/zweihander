---
name: yolo-push
description: Run a guarded commit-to-deploy workflow that verifies branch freshness, invokes commit and create-pr, waits for green CI, invokes approve-pr, monitors CD, and reports final deployment state. Use when the user asks to yolo-push, ship current changes, or execute the full PR-to-deployment flow.
disable-model-invocation: true
---

# YOLO Push

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
- [ ] Step 9: Report the final CD status, deployment URL or environment when
  available, and any failed stage logs or links.

## Non-Negotiable Stops

- Approve only when CI is green or not configured.
- Do not bypass, override, retry-loop indefinitely, or reinterpret red CI as
  acceptable.
- Do not ask for confirmation to continue past red or unknown CI.
- Do not claim shipped until CD reaches a clear success state when CD is
  configured; otherwise report CD as not configured.

## Reporting

Use terse status updates:

- `Committed: <sha>`
- `PR: <url>`
- `CI: waiting | green | not configured | failed <stage>`
- `Merge: merged | stopped`
- `CD: waiting | succeeded <environment> | not configured | failed <stage>`
