---
name: create-pr
description: Create a pull request from the current branch. Activate when user asks to create a PR, open a pull request, submit for review, or says /create-pr.
metadata:
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Create Pull Request

## Harness Adaptation

Identify the active assistant harness before applying this skill. If
harness-specific adaptation is needed, load exactly one matching metadata-linked
harness reference, then skip all non-matching harness files. A harness with no
matching metadata link uses the shared Claude Code-baseline workflow as written.

## Instructions

1. **Detect optional ticket ID** from current branch name:
   - `git branch --show-current`
   - Branch format: `<type>/<TICKET-ID>-short-description` (e.g., `feat/1234-add-feature`)
   - Parse ticket ID: `feat/1234-add-feature` → `1234`
   - Use the ticket ID only when the branch clearly contains one
   - If no ticket is found, proceed without asking for one
   - Ask for a ticket ID only when the user explicitly requests ticket-backed PR behavior and no ticket can be detected

2. **Fetch ticket context** (if ticket exists):
   - Use `<platform-cli>` to fetch ticket details as secondary context when a ticket was detected or explicitly requested
   - Code changes take priority for the title

3. **Analyze code changes** (primary source for PR title):
   - Commits: `git log develop..HEAD --oneline`
   - Diff summary: `git diff develop...HEAD --stat`
   - Full diff: `git diff develop...HEAD`
   - Focus on what changed in code

4. **Generate PR title**:
   - Prioritize actual code changes over ticket description
   - Handles follow-up/leftover work after main ticket work already merged
   - With ticket: `<TICKET-ID>: <concise summary>` (e.g. `1234: bump dependency to 2.0.33`)
   - No ticket: just `<concise summary>`
   - Keep it short and descriptive

5. **Generate PR body**:
   - Explain why the change exists: the problem, intent, or intuition behind the change
   - Summarize the material code/documentation changes
   - Use a Markdown checklist only for validation:
     - Checked items (`- [x]`) are validations already completed
     - Unchecked items (`- [ ]`) are validations still to be completed
   - Keep the body factual and scoped to observed changes; do not invent product impact or ticket details

6. **Create PR**:
   - Use `<platform-cli>` to create the PR with the generated title and generated body

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

- Never mention the assistant runtime in the PR title
- Ticket context is optional by default; do not ask for a ticket unless the user explicitly requests ticket-backed PR behavior
- After creating the PR, display a clickable hyperlink to the PR URL in the final message
