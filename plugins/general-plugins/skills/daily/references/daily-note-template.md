# Daily Note Template

The output file is `daily-DD-MM-YYYY.md`. Adapt sections based on which sources returned data — omit empty sections entirely.

## Hyperlinks

Every item referenced in the note must include a hyperlink to its source. This is non-negotiable — the daily note is a reference document, and readers need one-click access to evidence.

| Source | Link format |
|--------|-------------|
| Git commit | `https://{platform-url}/commit/{full-hash}` or local `git show {hash}` |
| Azure DevOps PR | `https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}` |
| Azure DevOps Work Item | `https://dev.azure.com/{org}/{project}/_workitems/edit/{id}` |
| Azure DevOps Pipeline | `https://dev.azure.com/{org}/{project}/_build/results?buildId={id}` |
| GitHub PR | `https://github.com/{owner}/{repo}/pull/{number}` |
| GitHub Issue | `https://github.com/{owner}/{repo}/issues/{number}` |
| GitHub Actions Run | `https://github.com/{owner}/{repo}/actions/runs/{run-id}` |
| GitLab MR | `https://{gitlab-host}/{group}/{repo}/-/merge_requests/{number}` |
| GitLab Issue | `https://{gitlab-host}/{group}/{repo}/-/issues/{number}` |
| GitLab Pipeline | `https://{gitlab-host}/{group}/{repo}/-/pipelines/{id}` |
| Slack message | Deep link if available from MCP, otherwise channel name only |
| Teams message | Deep link if available from MCP, otherwise team/channel name only |

Build the base URLs from context extracted during source detection (org, project, repo, host).

## Template

```markdown
# Daily Note — {DD-MM-YYYY} ({Day of Week})

> Window: {DD-MM-YYYY} 06:00 — {DD-MM-YYYY} {HH:MM}

## TL;DR

**Yesterday:** {1-3 bullet points — what was actually accomplished, derived from commits, merged PRs, and resolved work items in the window}

**Today:** {1-3 bullet points — what's planned next, derived from active PRs needing attention, in-progress work items, and dirty worktrees with pending work}

**Blockers / Concerns:** {bullet points if any, otherwise "None"}

---

## Summary

{2-3 sentence high-level summary of the day's activity. What was the main focus? Any blockers or highlights?}

## Git Activity

{Only if git source returned data}

### Commits
- [`{short-hash}`]({link-to-commit}) {commit message} (`{branch}`)
- ...

### Branches touched
- `{branch-name}` — {what changed, 1 line}

### Worktrees
{Only if worktrees exist beyond the main one}
- `{worktree-path}` on `{branch}` — {status: ahead/behind/clean}

## Pull Requests

{Section name adapts to platform: "Pull Requests" for GitHub/Azure DevOps, "Merge Requests" for GitLab}

### Created
- [**#{id}**]({link}) {title} → `{target-branch}` ({status})

### Updated
- [**#{id}**]({link}) {title} — {what happened: new comments, approvals, pushes}

### Merged / Completed
- [**#{id}**]({link}) {title} — merged into `{branch}`

## Tasks / Work Items

{Adapts to platform: "Work Items" for Azure DevOps, "Issues" for GitHub/GitLab}

### Assigned to me
- [**#{id}**]({link}) {title} ({state}) — {brief context if available}

### Status changes
- [**#{id}**]({link}) {title}: {old-state} → {new-state}

### New comments
- [**#{id}**]({link}) {title} — {commenter}: "{comment preview, first ~80 chars}"

## CI/CD

{Only if pipeline/workflow runs happened within the window. Only include pipelines associated with the current repository — exclude builds from other repos in the same project/org.}

- [**{pipeline-name}** #{number}]({link}) — {result: succeeded/failed} (`{branch}`) {start}–{end} UTC

## Messages

{One subsection per messaging source: Slack, Teams, Telegram, etc. Only if data was fetched.}

### {Source Name}
- **#{channel}** — {summary of relevant messages or threads}

## Notes

{Any additional context, blockers, or items to follow up on tomorrow. Leave blank if nothing to add.}
```

## Guidelines

- The **TL;DR section** is the first thing people read — it follows classical standup structure. "Yesterday" is synthesized from actual completed work in the window (not just a list of commits). "Today" is inferred from what's in-progress or next up. "Blockers" captures failed pipelines, stale PRs, or anything that might need escalation.
- Every PR, issue, work item, commit, and pipeline run must be a clickable markdown link
- Keep it factual, not narrative — this is a reference document, not a story
- Use the DD-MM-YYYY date format everywhere in the note
- If a hyperlink cannot be constructed (e.g. messaging source doesn't provide deep links), use the item title/name as plain text
- If a source failed, add a note at the bottom: `> Source {name} was unavailable: {reason}`
- Prefer bullet points over paragraphs
- The Summary section is the most important — write it last, after all data is gathered
