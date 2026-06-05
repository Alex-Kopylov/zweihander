---
name: ticket-comment-status
description: Post a status update comment to a work item or issue. Activate when user asks to update a task, write a status comment, post progress, or says /ticket-comment-status.
metadata:
  ai-assistant-harness-adaptation.claude-code: references/ai-assistant-harnesses/claude-code.md
  ai-assistant-harness-adaptation.codex: references/ai-assistant-harnesses/codex.md
---

# Post Status Update to Work Item

Write a concise, PM/customer-friendly status update and post it as a comment on the linked work item.

## Harness Adaptation

Identify the active assistant harness before following this workflow. When harness-specific adaptation is needed, load exactly one matching metadata-linked harness reference and skip every non-matching harness file.

## Instructions

1. **Extract work item ID** from current branch name:
   - `git branch --show-current`
   - Branch format: `<type>/<ID>-short-description` (e.g., `feat/6877-risk-summary`)
   - Parse work item ID: `feat/6877-risk-summary` → `6877`
   - If no ID found → ask user

2. **Gather context** (run in parallel):
   - Commits: `git log develop..HEAD --oneline`
   - Diff summary: `git diff develop...HEAD --stat`
   - Unstaged/uncommitted: `git status --porcelain`
   - Read plan files if they exist: `docs/plans/` directory

3. **Draft the update**:
   - Write for a PM or customer who knows nothing about the codebase
   - Bullet points, not paragraphs
   - Lead with what the feature does for the user, not implementation details
   - No file names, no class names, no internal jargon
   - No commit counts, line counts, or file counts
   - Mention "unit tests in place" if tests exist — never list test details
   - End with a numbered **Remaining** list if work is incomplete
   - Keep the entire comment under 10 lines

4. **Ask user to confirm** the drafted comment before posting — always, no exceptions

5. **Post the comment**:
   - Use `<platform-cli>` to add a comment to the work item/issue
   - Format: `markdown`
   - Work item ID: from step 1
   - Alternatives: ADO MCP tools, `gh issue comment`, `glab issue note`

## Example

```markdown
**Status Update**

- Core implementation complete — new endpoint generates professional analysis text for the report
- LLM acts strictly as an editor: polishes raw input without inventing content
- Async processing with caching and observability, follows existing proven patterns
- Unit tests in place

**Remaining:**
1. Optimize prompts
2. Integration tests
3. Local end-to-end testing
4. Test on dev environment
```

## Notes

- Bold the heading (`**Status Update**`) — no markdown H1/H2 in comments
- "Remaining" section is optional — omit if work is fully complete
