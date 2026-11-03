---
name: create-pr
description: Create a pull request from the current branch. Activate when user asks to create a PR, open a pull request, submit for review, or says /create-pr.
metadata:
  references:
    "references/github.md": "Load when the pull request is created on GitHub."
---

# Create Pull Request

## Modes

- **push** (default): push the branch, then create the PR. Applies unless
  the user explicitly says otherwise.
- **preview**: when the user asks to preview, show the generated title and
  body and stop. Push nothing and create nothing.

## Instructions

1. **Detect optional ticket ID** from current branch name:
   - `git branch --show-current`
   - Branch format: `<type>/<TICKET-ID>-short-description` (e.g., `feat/1234-add-feature`)
   - Parse ticket ID: `feat/1234-add-feature` → `1234`
   - Use the ticket ID only when the branch clearly contains one
   - If no ticket is found, proceed without asking for one
   - Ask for a ticket ID with $request_user_input only when the user explicitly requests ticket-backed PR behavior and no ticket can be detected

2. **Fetch ticket context** (if ticket exists):
   - Use `<platform-cli>` to fetch ticket details as secondary context when a ticket was detected or explicitly requested
   - Code changes take priority for the title

3. **Resolve the base branch**: the branch the PR targets. Use the branch
   the user names; otherwise the repository's default branch
   (`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` on
   GitHub). Never hard-code a name.

4. **Analyze code changes** (primary source for PR title):
   - Commits: `git log <base>..HEAD --oneline`
   - Diff summary: `git diff <base>...HEAD --stat`
   - Full diff: `git diff <base>...HEAD`
   - Focus on what changed in code

5. **Generate PR title**:
   - Prioritize actual code changes over ticket description
   - Handles follow-up/leftover work after main ticket work already merged
   - With ticket: `<TICKET-ID>: <concise summary>` (e.g. `1234: bump dependency to 2.0.33`)
   - No ticket: just `<concise summary>`
   - Keep it short and descriptive

6. **Generate PR body**:
   - Use these `##` headers, in this order: What Problem This Solves, Why This Change Was Made, User Impact, Evidence
   - Write Evidence as a Markdown checklist of validations, where `- [x]` is done and `- [ ]` is still to do
   - Keep the body factual and scoped to observed changes; do not invent product impact or ticket details

7. **Push** (push mode only): `git push -u origin HEAD`. In preview mode,
   show the title and body and stop here.

8. **Create PR** (push mode only):
   - Use `<platform-cli>` to create the PR against `<base>` with the generated title and generated body

9. **Report**:
   - In the final message, summarize what was done as a short, nicely formatted bullet list

## Examples

**Single commit branch:**
- Branch: `feat/1234-pydantic-bump`
- Commit: `1234: bump pydantic to 2.10.0`
- PR title: `1234: pydantic version bump to 2.10.0`

**Multi-commit follow-up branch:**
- Branch: `fix/5678-merchant-screening`
- Commits: fix lint errors, update test snapshots
- Ticket: "Implement merchant screening workflow"
- PR title: `5678: fix lint errors and update test snapshots`
  (code changes prioritized over ticket description)

## Notes

- Never mention the AI agent in the PR title
- Ticket context is optional by default; do not ask for a ticket unless the user explicitly requests ticket-backed PR behavior
- After creating the PR, display a clickable hyperlink to the PR URL in the final message
