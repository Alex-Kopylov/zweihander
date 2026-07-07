---
name: yolo-push
description: Run a guarded commit-to-deploy workflow that verifies branch freshness, invokes commit and create-pr, waits for green CI, invokes approve-pr, monitors CD, and reports final deployment state. Use when the user asks to yolo-push, ship current changes, or execute the full PR-to-deployment flow.
---

# YOLO Push

## Workflow

Progress:

- [ ] Step 1: Ensure the local branch is up-to-date. Stop on divergence,
  missing upstream, or unknown freshness.
- [ ] Step 2: Invoke `dev-workflow:commit` to create the commit.
- [ ] Step 3: Invoke `dev-workflow:create-pr` to open the PR.
- [ ] Step 4: Stop and wait for CI to finish.
- [ ] Step 5: If any CI stage is failed, canceled, missing, still pending after
  the platform timeout or agreed wait, or not green, stop and fail loudly with
  the failing stage names and PR link.
- [ ] Step 6: Invoke `dev-workflow:approve-pr`.
- [ ] Step 7: Monitor CD/deployment status until it reaches a terminal state.
- [ ] Step 8: Report the final CD status, deployment URL or environment when
  available, and any failed stage logs or links.

## Non-Negotiable Stops

- Do not approve or merge before CI is fully green.
- Do not bypass, override, retry-loop indefinitely, or reinterpret red CI as
  acceptable.
- Do not ask for confirmation to continue past red or unknown CI.
- Do not continue to approval when CI status cannot be found.
- Do not claim shipped until CD reaches a clear success state.

## Reporting

Use terse status updates:

- `Committed: <sha>`
- `PR: <url>`
- `CI: waiting | green | failed <stage>`
- `Merge: merged | stopped`
- `CD: waiting | succeeded <environment> | failed <stage>`
