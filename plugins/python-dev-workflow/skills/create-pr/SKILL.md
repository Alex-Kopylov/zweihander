---
name: create-pr
description: ""
---

# Create Pull Request

## Instructions

1. **Extract ticket ID** from current branch name:
   - `git branch --show-current`
   - Branch format: `<type>/<TICKET-ID>-short-description` (e.g., `feat/1234-add-feature`)
   - Parse ticket ID: `feat/1234-add-feature` → `1234`
   - If no ticket found → ask user for ticket ID
   - Only skip ticket if user **explicitly** says "no ticket"

2. **Fetch ticket context** (if ticket exists):
   - Use `<platform-cli>` to fetch ticket details for background context
   - This is secondary info — code changes take priority for title

3. **Analyze code changes** (primary source for PR title):
   - Commits: `git log develop..HEAD --oneline`
   - Diff summary: `git diff develop...HEAD --stat`
   - Full diff: `git diff develop...HEAD`
   - Focus on the essence of what actually changed in code

4. **Generate PR title**:
   - Prioritize actual code changes over ticket description
   - Handles cases where main ticket work already merged and this is follow-up/leftovers
   - With ticket: `<TICKET-ID>: <concise summary>` (e.g. `1234: bump dependency to 2.0.33`)
   - No ticket: just `<concise summary>`
   - Keep it short and descriptive

5. **Create PR**:
   - Use `<platform-cli>` to create the PR with the generated title and empty body
   - Alternatives: `gh` for GitHub, `glab` for GitLab

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

- PR body is always empty
- Never mention claude in PR title
- Ticket number is required unless user explicitly says there is none
